#!/usr/bin/env python

#from collections import defaultdict
import sys
import os
import subprocess
import yaml
import glob
#from re import match

YAMLTEMPLATE="""!include common.yaml
---
- package: %s Perl module 
  name: %s
  version: "%s"
  vendor_source: %s
  description: >
    %s perl module. %s
"""

# borrow this class from R-admix, update as needed
class Node(object):
    def __init__(self, name):
        self.name = name     # perl name with "::
        self.edges = []
    def addEdge(self, node):
        self.edges.append(node)

    def resolve(self,resolved):
        for edge in self.edges:
            if edge not in resolved:
                edge.resolve(resolved)
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
        print ("NAME", self.perlname, "parent=%d: %s" % (self.rename,self.mainModule), "Version", self.version)
        print ("    PREREQS", self.prereqs)
        print ("download", self.download)
        print ("provides", self.provides)
        print ("prereqs", self.prereqs)

    def getName(self):
        return (self.name, self.perlname)

    def getPrereqs(self):
        return self.prereqs

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
        self.name        = data["metadata"]['name'] # notation where "::" is changed to "-"
        self.provides    = data['provides']
        self.download    = data['download_url']
        description = data['abstract']
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
            rPrereqs = prereqs['runtime']['requires']
        except:
            rPrereqs = {}

        self.prereqs = cPrereqs.copy()
        self.prereqs.update(rPrereqs)

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
        helpstr = "NAME\n        %s - create perl modules dependency list \n" % self.prog \
                + "\nSYNOPSIS\n        %s FILE\n" % self.prog \
                + "\nDESCRIPTION\n" \
                + "        Collect information about perl system installed modules on the host using 'cpan -l'. \n" \
                + "        FILE - list of perl modules to install one per line  \n" \
                + "        For each module name in FILE, get cpan info about the module and build a \n\n" \
                + "        module dependency ordered list.  \n\n" \
                + "        -h, --h, --help, help\n              Print usage info.\n\n"

        print (helpstr)
        sys.exit(0)

    def getCpanList(self):
        '''Parse the output of the 'cpan -l' command and create a dictionary of system installed modules '''
        p = subprocess.Popen( self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, error) = p.communicate()

        # split string into lines and remove first header line
        self.lines = output.decode('utf-8').splitlines()[1:]

        for l in self.lines:
            items = l.split()
            if len(items) == 2:
                if items[1] == "undef":
                     version = "-1"
                else:
                     version = items[1]
                self.syspkgs[items[0]] = version
            else:
                print ("ERROR", l) # line should have name and version

    def getDesiredList(self):
        ''' get a list of desired modules from the file '''
        if not os.path.isfile(self.fname):
            self.exitHelp()
        f = open(self.fname)
        txt = f.read()
        f.close()
        lines = txt.splitlines()
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
        #for k,v in self.namemap.items():
        #    print ("MAP", k, v)

        print ("modnames", len (self.modnames), "prereqs=", len(self.depends), "desired=", len(self.desired)) 
        for k,v in self.desired.items():
            print (k, v.getVersion())

    def createNodes(self):
        for k in self.desired.keys():
            self.nodes.append(Node(k))

        # make a  master Node to and add all edges to it to make sure that the dependency graph is connected
        master = Node('root')
        for node in self.nodes:
            master.addEdge(node)
            deps = self.desired[node.name].getPrereqs()
            #DEBUG print ("for NODE", node.name, deps)
            try:
                edges = filter(lambda x: x.name in deps, self.nodes)
                for edge in edges:
                    node.addEdge(edge)
                    #DEBUG print ("    add EDGE", edge.name)
            except:
                pass

        # resolve the order
        resolved = [] 
        master.resolve(resolved)
        self.resolved = resolved

    def writeYaml(self):
        self.checkFilters()
        order=open("buildorder","w")
        
        for pkg in self.resolved[:-1]: # dont look at the 'root' node
            mod = self.desired[pkg.name]
            name, perlname = mod.getName()
            order.write("%s\n" % name)
            txt = YAMLTEMPLATE % (perlname, name, mod.getVersion(), mod.getDownload(), perlname, mod.getDescription())
            txt += self.writeAddFiles(pkg.name)
            txt += self.writePrereqs(mod)
            #FIXME name
            print ("Writing auto-%s.yaml" % name)
            f = open('auto-%s.yaml' % name, "w")
            f.write(txt)
            f.close()

        order.close()

    def writePrereqs(self, mod):
        ''' write prerequisites modues if any '''
        txt = ""
        for i in mod.getPrereqs().keys():
            txt += "    - perl_{{ versions.perl }}-%s\n" % i.replace("::","-")
        if txt:
           txt = "  requires:\n    - perl_{{ versions.perl }}\n" + txt

        return txt

    def writeAddFiles(self, name):
        ''' if there are specifc filters for the module 
            overwrite defaults '''
        txt = ""
        p = filter(lambda x: name in x, self.filterProvides)
        r = filter(lambda x: name in x, self.filterRequires)

        if p or r:
            txt = "  addfile:\n     - listRpmFiles.py\n" + txt
            if not p: 
                p = self.self.defaultProvides
            if not r:
                r = self.defaultRequires
            txt += "    - %s\n" % p
            txt += "    - %s\n" % r

        return txt 
        

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

        self.createNodes()
        self.writeYaml()

        self.printInfo()


##### Run from a command line #####
if __name__ == "__main__":
    app = BuildDepend(sys.argv)
    app.run()
