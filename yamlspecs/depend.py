#!/usr/bin/env python

import sys
import os
import subprocess
import yaml
import glob
import re

YAMLTEMPLATE="""!include common.yaml
---
- package: %s Perl module 
  name: %s
  version: "%s"
  vendor_source: %s
  description: >
    %s perl module. %s
"""

RPMEXTRATEMPLATE="""  rpm:
    extras: |
      %define _python_bytecompile_errors_terminate_build 0\\n\\
      %define __spec_install_post \\
      %{?__debug_package:%{__debug_install_post}}\\
      module load {{build.modules}};\\
      %{__arch_install_post}\\
      %{__os_install_post}\\
      module unload {{build.modules}}\\
      %{nil}\\n\\
      %define _use_internal_dependency_generator 0\\n\\
      %define __find_requires %{_builddir}/%{name}-%{version}/REQUIRES\\n\\
      %define __find_provides %{_builddir}/%{name}-%{version}/PROVIDES\\n\\
      %global __provides_exclude_from %{perl_vendorarch}/auto/.*\\\\.so$|%{perl_archlib}/.*\\\\.so$|%{_docdir}\\n\\
      %global __requires_exclude_from %{_docdir}
"""

# borrow this class from R-admix, update as needed
class Node(object):
    def __init__(self, name):
        self.name = name     # perl name with "::
        self.edges = []
    def addEdge(self, node):
        self.edges.append(node)

    def resolve(self,resolved, level):
        print ("EDGE", level, self.name, len(self.edges))
        for edge in self.edges:
            if edge not in resolved:
                level += 1
                edge.resolve(resolved, level)
        resolved.append(self)


# This is an object for the perl module info collected from cpan
class ModInfo(object):
    def __init__(self, name):
        self.perlname = name   # perl notation, i.e. Try::Tiny
        self.version = None
        self.download = None
        self.cmd = ['perl', 'getinfo.pl', self.perlname]
        self.rename = 0  # flag 

        self.getCpanModInfo()

    def printInfo(self):
        # for debugging only
        print ("NAME", self.perlname, "parent=%d: %s" % (self.rename,self.mainModule), "Version", self.version)
        print ("    PREREQS", self.prereqs)
        print ("download", self.download)
        print ("provides", self.provides)
        print ("prereqs", self.prereqs)

    def getName(self):
        return (self.name, self.perlname)

    def getPrereqs(self):
        return (self.prereqs)

    def getRename(self):
        return (self.rename)

    def getMainMod(self):
        return (self.mainModule)

    def getVersion(self):
        return (self.version)

    def getDownload(self):
        return (self.download)

    def getDescription(self):
        return (self.description)

    def getCpanModInfo(self):
        '''Parse the output of the perl command '''
        #print ("DEBUG workling on ", self.perlname)
        p = subprocess.Popen( self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, error) = p.communicate()

        # discard perl "blessed" part that has illegal !! in yaml
        # leave only what we need to process
        index = output.find("\ndata:")
        output = "---" + output[index:]

        if error: #FIXME
            print (error)

        info = yaml.load(output)
        data = info['data']

        # the requested module is provided by another parent main module
        try: 
            self.mainModule = data['main_module']
            if self.mainModule != self.perlname:
                self.rename = 1
        except:
            pass
        
        self.version     = data['version']
        self.name        = data['distribution'] # notation where "::" is changed to "-"
        self.provides    = data['provides']
        self.download    = data['download_url']
        try: 
            description = re.sub("`", "'", data['abstract']) # rm back single quote, they break RPM build
        except:
            description = "Lazy perl programmers did not bother to make one"

        # rm unicode characters
        try:
            # python 3
            self.description = description.encode('ascii', 'ignore') 
        except:
            # python 2
            self.description = description.decode('unicode_escape').encode('ascii','ignore')

        # some perl packages don't provide prereqs
        try:
            prereqs      = data['metadata']['prereqs']
        except:
            self.prereqs = {} 
            return

        try:
            # from configure phase
            cPrereqs = prereqs['configure']['requires']
        except:
            cPrereqs = {}
        try:
            # from runtime phase
            #phase1 = {}
            #phase2 = {}
            #if 'requires' in prereqs['runtime']:
            #    phase1 = prereqs['runtime']['requires']
            #if 'suggests' in prereqs['runtime']:
            #    phase2 = prereqs['runtime']['suggests']
            #rPrereqs = phase1.copy()
            #rPrereqs.update(phase2)
            rPrereqs = prereqs['runtime']['requires']
	except:
            rPrereqs = {}

        self.prereqs = cPrereqs.copy()
        self.prereqs.update(rPrereqs)
        #print ("DEBUG HERE", self.name, self.prereqs.keys())

    def updatePrereqs(self, syspkgs):
        ''' check against the list of system modules and update prerequisites '''
        instnames = syspkgs.keys()  # names of system perl modules currently avail 

        # rm perl from prereqs
        if 'perl' in self.prereqs.keys():
            self.prereqs.pop('perl')

        # check module prereqs vs system installed 
        for k in self.prereqs.keys():
	    if k in instnames:
               if self.prereqs[k] < syspkgs[k]: 
                   del self.prereqs[k] # system installed version is sufficient, rm module from prereqs

    def updatePrereqsMap(self, mmap):
        ''' update prereqs according to the names in mmap '''
        mapkeys = mmap.keys()
        result = {}
        for k, v in self.prereqs.items():
            if k in mapkeys:
                modname, modversion = mmap[k]
                result[modname] = modversion # use updated name/version
            else:                  
                result[k] = v                # use existing name/version

        self.prereqs = result

class BuildDepend(object):
    def __init__(self, args=None):
        self.args = args
        self.cmd = ['cpan', '-l']
        self.syspkgs = {}   # default installed system perl modules 
        self.modnames = []  # list of desired module names, will get from input file 
        self.desired = {}   # dictionary of desired modules, keys: mod names, values: ModInfo objects 
        self.depends = {}
        self.nodes = []     # graph nodes
        self.sysperl = 'sysperl'  # default file that contains info about modules installed with perl RPM

        self.parseArgs()

    def parseArgs(self):
        self.prog = self.args[0]
        if len(self.args) == 1:
            self.exitHelp()
        if self.args[1] in ["-h","--h","help","-help","--help"]:
            self.exitHelp()
        self.fname = self.args[1]
        return

    def exitHelp(self):
        helpstr = "NAME\n        %s - create perl modules yaml files and ordered dependency list\n" % self.prog \
                + "\nSYNOPSIS\n        %s FILE\n" % self.prog \
                + "\nDESCRIPTION\n" \
                + "        Check information about installed perl modules on the host from a 'sysperl' file.\n" \
                + "        Assume 'sysperl file is in the current directory where this program is run. \n" \
                + "        The 'sysperl file is generated via running 'cpan -l > sysperl' command. \n\n" \
                + "        FILE - a file with perl modules names (perl notation using ::) to install, one name \n" \
                + "        per line. For each module name in FILE, get cpan info about the module, create a yaml\n" \
                + "        file for it, and a resulting module dependency ordered list. Modules found in 'sysperl'\n" \
                + "        will not be added to buildorder. \n\n" \
                + "        -h, --h, --help, help\n              Print usage info.\n\n" \
                + "\nOUTPUT\n" \
                + "        buildorder - a file with ordered module names that need to be build \n" \
                + "        MOD-NAME.yaml - yaml file for each MOD-NAME module listed in buildorder file.\n" \

        print (helpstr)
        sys.exit(0)

    def getCpanList(self):
        '''Parse the info about perl installed modules and create a dictionary of installed modules '''
        #p = subprocess.Popen( self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #(output, error) = p.communicate()

        # split string into lines and remove first header line
        #self.lines = output.decode('utf-8').splitlines()[1:]
        lines = self.readFile(self.sysperl)

        for l in lines:
            items = l.split()
            if len(items) == 2: # module name and version
                if items[1] == "undef":
                     version = "-1"
                else:
                     version = items[1]
                self.syspkgs[items[0]] = version
            else:
                continue  # skip cpan logging or other lines

    def readFile(self, fname):
        ''' read file and return read lines'''
        if not os.path.isfile(fname):
            print ("File %s not found" % fname)
            self.exitHelp()
        f = open(fname)
        txt = f.read()
        f.close()
        lines = txt.decode('utf-8').splitlines()
        return (lines)

    def getDesiredList(self):
        ''' get a list of desired modules from the file '''
        #if not os.path.isfile(self.fname):
        #    self.exitHelp()
        #f = open(self.fname)
        #txt = f.read()
        #f.close()
        #lines = txt.splitlines()
        lines = self.readFile(self.fname)
        for l in lines:
            if l[0] == "#": continue  # skip comment ines
            name = ''.join(l.split()) # rm white spaces
            self.modnames.append(name)

    def getPrereqs(self, modnames):
        ''' for desired module names find their prerequisite modules '''
        for name in modnames:
            print ("Working on", name)
            mod = ModInfo(name)
            mod.updatePrereqs(self.syspkgs)    
            #mod.printInfo()    
            self.desired[name] = mod
            self.addPrereqs(mod)

    def addPrereqs(self, mod):
        ''' update overall dependencies by adding found in the mod '''

        # combine dependencies so far collected and add any new from the mod
        # based on higher value for the common keys. If the mod name is found
        # in dependencies, clear it (already is desired list)

        dict1 = mod.getPrereqs() # dependencies from the mod
        dict2 = self.depends     # current collected dependencies
        # this does not work in python2
        #result = {key: dict1.get(key, 0) if dict1.get(key, 0) > dict2.get(key, 0) else dict2.get(key,0) for key in set(dict1) | set(dict2)}
        for k,v in dict1.items():
            if k in self.depends: 
                if self.depends[k] < v:
                    self.depends[k] = v  
            else:
               self.depends[k] = v

        # find main module name
        perlname = mod.getMainMod()
        if perlname in self.depends:
            del self.depends[perlname]
          
    def createMap(self):
        # remap desired modules names according to their main modules 
        self.namemap = {}
        modnames = self.desired.keys()
        result = {}
        for m in modnames:
            mod = self.desired[m]
            if mod.getRename():
                parent = mod.getMainMod()
                version = mod.getVersion()
                self.namemap[m] = (parent, version)
                result[parent] = mod
            else:
                result[m] = mod

        self.desired = result

    def mapPrereqs(self):
        # remap rereqs names according to the names in map
        if self.namemap == {}:
            return
        
        for k in self.desired.keys():
            mod = self.desired[k]
            mod.updatePrereqsMap(self.namemap)

    def allPrereqs(self):
        self.getPrereqs(self.modnames)
        modnames = self.depends.keys()
        # get cpan info on all prereqs till all are accounted 
        while len(modnames):
            self.getPrereqs(modnames)
            modnames = [x for x in self.depends.keys() if x not in self.desired.keys()]

        # create mapping for renaming modules and rename all prereqs
        self.createMap()
        self.mapPrereqs()

    def printInfo(self):
        for k,v in self.namemap.items():
            print ("MAP", k, v)

        #print ("modnames", len (self.modnames), "prereqs=", len(self.depends), "desired=", len(self.desired)) 
        #for k,v in self.desired.items():
        #    print (k, v.getVersion())
        pass

    def createNodes(self):
        for k in self.desired.keys():
            self.nodes.append(Node(k))

        # make a  master Node to and add all edges to it to make sure that the dependency graph is connected
        master = Node('root')
        resolved = [] 
        for node in self.nodes:
            master.addEdge(node)
            deps = self.desired[node.name].getPrereqs()
            if not deps:
                resolved.append(node)
            print ("DEBUG NODE prereqs ", node.name, deps)
            try:
                edges = filter(lambda x: x.name in deps, self.nodes)
                for edge in edges:
                    node.addEdge(edge)
                    #DEBUG print ("    add EDGE", edge.name)
            except:
                pass

        # resolve the order
        #resolved = [] 
        print ("RESOLVED start length", len(resolved))
        master.resolve(resolved, 0)
        self.resolved = resolved

    def writeYaml(self):
        #self.checkFilters()
        fo = open("buildorder","w")
        order = ""
        
        for pkg in self.resolved[:-1]: # dont look at the 'root' node
            mod = self.desired[pkg.name]
            name, perlname = mod.getName()
            version = mod.getVersion()
            fullUrl = mod.getDownload()
            i = fullUrl.rfind("/") + 1
            distrofile = fullUrl[i:]
            schemaname = "%s-%s.tar.gz" % (name, version)
            if  distrofile == schemaname:
                url = fullUrl[:i] + "{{name}}-{{version}}.{{extension}}"
            else:
                url = fullUrl
            txt = YAMLTEMPLATE % (perlname, name, version, url, perlname, mod.getDescription())
            
            # Next 2 were for previous filter writing. Currently, filters are
            # added in the yaml afterwards, there is no way to automate the addition
            #txt += self.writeAddFiles(pkg.name)
            #txt += self.writePrereqs(mod)

            prefname = name
            order += "%s\n" % prefname
            print ("Writing %s.yaml" % prefname)
            f = open('%s.yaml' % prefname, "w")
            f.write(txt)
            f.close()

        fo.write(order)
        fo.close()

    def writeVersions(self):
        verfile=open("versions-desired","w")
        txt = "The install the specified desired perl modules:\n"
        for i in self.modnames:
            txt += "\t%s\n" % i
        txt += "\nthe following packages and their versions will need to be installed:\n"
        for pkg in self.resolved[:-1]: # dont look at the 'root' node
            mod = self.desired[pkg.name]
            name, perlname = mod.getName()
            modver = mod.getVersion()
            #verfile.write("%s: %s\n" % (name, modver))
            txt += "%s: \"%s\"\n" % (name, modver)

        verfile.write(txt)
        verfile.close()


    def writePrereqs(self, mod):
        ''' write prerequisites modules if any '''
        # add perl as a requirement to all yaml files
        txt = "  requires:\n    - perl_{{versions.perl}}\n" 
        for i in mod.getPrereqs().keys():
            txt += "    - perl_{{versions.perl}}-%s\n" % i.replace("::","-")

        return (txt)

    def writeAddFiles(self, fullname):
        ''' if there are specifc filters for the module 
            overwrite defaults '''
        name = fullname.replace("::","-")
        txt = ""
        rpmtxt = ""
        p = filter(lambda x: name in x, self.filterProvides)
        r = filter(lambda x: name in x, self.filterRequires)

        if p or r:
            txt = "  addfile:\n    - listRpmFiles.py\n" + txt
            if p: 
                p = p[0]
            else:
                p = self.defaultProvides
            if r:
                r = r[0]
            else:
                r = self.defaultRequires
            txt += "    - %s\n" % p
            txt += "    - %s\n" % r
            # rewrite extra rpm with updated filters
            rpmtxt += self.writeExtraRPM(p,r)

        txt += rpmtxt
        return (txt)
        
    def writeExtraRPM(self, p, r):
        txt = RPMEXTRATEMPLATE.replace("PROVIDES", p).replace("REQUIRES", r)
        return (txt)

    def checkFilters(self):
        # check provides filters available
        fp = glob.glob('filter-provides*.sh.in')
        fp = list(map(lambda x: x.replace('.in',''),fp))
        self.filterProvides = filter(lambda x: 'perl' not in x, fp)
        self.defaultProvides = 'filter-provides-perlmodules.sh'

        # check requires filters available
        fr = glob.glob('filter-requires*.sh.in')
        fr = list(map(lambda x: x.replace('.in',''),fr))
        self.filterRequires = filter(lambda x: 'perl' not in x, fr)
        self.defaultRequires = 'filter-requires-perlmodules.sh'

    def run(self):
        self.getCpanList()
        self.getDesiredList()
        self.allPrereqs()
        print ("MAPPING", self.namemap)

        self.createNodes()
        self.writeYaml()
        self.writeVersions()

        self.printInfo()


##### Run from a command line #####
if __name__ == "__main__":
    app = BuildDepend(sys.argv)
    app.run()
