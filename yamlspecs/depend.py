#!/usr/bin/env python

from collections import defaultdict
import sys
import os
import subprocess
import yaml
from re import match

class ModInfo:
    def __init__(self, name):
        self.perlname = name
        #self.name = self.perlname.replace("::",'-')
        self.version = None
        self.download = None
        self.cmd = ['perl', 'getinfo.pl', self.perlname]

        self.readCpanInfo()

    def printInfo(self):
        print ("NAME", self.name)
        print ("VERSION", self.version)
        print ("download", self.download)
        print ("provides", self.provides)
        print ("depend-config", self.confPrereqs)
        print ("depend-runtime", self.runPrereqs)

    def readCpanInfo(self):
        '''Parse the output of the perl command '''
        print ("workling on ", self.perlname)
        p = subprocess.Popen( self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, error) = p.communicate()
        # discard perl "blessed" part, leave only what we need to process
        firstData = output.find("\ndata:")
        output = "---" + output[firstData:]

        if error:
            #TODO
            print (error)

        info = yaml.load(output)
        data = info['data']
        
        self.version     = (data['version'])
        self.name        = (data["metadata"]['name'])
        self.provides    = (data['provides'])
        self.download    = (data['download_url'])
        self.description = (data['abstract'])
        prereqs          = data['metadata']['prereqs']
        self.confPrereqs = prereqs['configure']['requires']
        self.runPrereqs  = prereqs['runtime']['requires']


    def readModFile(self ):
        ''' get a list of desired modules from the file '''
        self.desired = {}

class BuildModInfo:
    def __init__(self, args=None):
        self.args = args
        self.cmd = ['cpan', '-l']
        self.default = {}   # default installed modules via perl RPM 
        self.modlist = []   # list of desired module names, will get from input file 
        self.dependsConf = {}
        self.dependsRun = {}

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
        helpstr = "NAME\n        %s - collect module info\n" % self.prog \
                + "\nSYNOPSIS\n        %s FILE\n" % self.prog \
                + "\nDESCRIPTION\n" \
                + "        Collect information about perl modules installed on the host using 'cpan -l'. \n" \
                + "        FILE - list of perl modules one per line  \n" \
                + "        When executing on a command line, outputs collected info on stdout.\n\n" \
                + "        -h, --h, --help, help\n              Print usage info.\n\n"

        print (helpstr)
        sys.exit(0)

    def readInfo(self):
        '''Parse the output of the 'cpan -l' command and create a dictionary of installed modules instances'''
        p = subprocess.Popen( self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, error) = p.communicate()

        # split string into lines and remove first header line
        self.lines = output.decode('utf-8').splitlines()[1:]

        for l in self.lines:
            items = l.split()
            if len(items) == 2:
                try: 
                    version = float(items[1])
                except:
                    version = -1
                self.default[items[0]] = version
            else:
                print ("ERROR", l)

    def readModFile(self ):
        ''' get a list of desired modules from the file '''
        self.desired = {}
        if not os.path.isfile(self.fname):
            self.exitHelp()
        f = open(self.fname)
        txt = f.read()
        f.close()
        lines = txt.splitlines()
        for l in lines:
            if l[0] == "#": continue  # skip comment ines
            name = ''.join(l.split()) # rm white spaces
            self.modlist.append(name)

    def getCpanInfo(self):
        for name in self.modlist:
            self.desired[name] = ModInfo(name)
            self.desired[name].printInfo()    
            self.dependsConf.update(self.desired[name].confPrereqs)
            self.dependsRun.update(self.desired[name].runPrereqs)


    def run(self):
        #self.readInfo()
        self.readModFile()
        self.getCpanInfo()
        print ("total conf prereqs", self.dependsConf)
        print ("total run prereqs", self.dependsRun)

##### Run from a command line #####
if __name__ == "__main__":
    app = BuildModInfo(sys.argv)
    app.run()
