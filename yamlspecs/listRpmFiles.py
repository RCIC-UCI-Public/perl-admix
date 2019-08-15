#!/usr/bin/env python

import sys
import os
import subprocess

class Listing:
    def __init__(self, args=None):
        self.args = args
        self.fname = "./LISTFILES" # output file name with files listing
        self.rmfile = ".packlist"  # perl build-created files not to include
        self.items = []            # names of files to put in LISTFIILES
        self.parseArgs()

    def parseArgs(self):
        self.prog = self.args[0]
        if len(self.args) < 1:
            self.exitHelp()
        if self.args[1] in ["-h","--h","help","-help","--help"]:
            self.exitHelp()
        self.buildpath = self.args[1]
        self.cmd = ['find', self.buildpath, '-type', "f", "-size", "+0"]
        self.index = len(self.buildpath)
        return

    def exitHelp(self):
        helpstr = "NAME\n        %s - find files in the PATH to include in RPM \n" % self.prog \
                + "\nSYNOPSIS\n        %s PATH\n" % self.prog \
                + "\nDESCRIPTION\n" \
                + "        RUn find commadn on the given PATH and find all the files to include in RPM. \n" \
                + "        PATH -  build directory of perl module\n" \
                + "        Writes file names in a LISTFILES file in the build direcory.\n\n" \
                + "        -h, --h, --help, help\n              Print usage info.\n\n"

        print (helpstr)
        sys.exit(0)

    def runCommand(self):
        '''Parse the output of the command and create a listing of files to include in RPM '''
        p = subprocess.Popen( self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, error) = p.communicate()

        # split string into lines 
        self.lines = output.decode('utf-8').splitlines()

        for l in self.lines:
            # remove ".packlist" files
            if l.find(self.rmfile) > 0: 
                try:
                    os.unlink(l)
                except OSError as e:  # should not be here
                    print ("Error: %s - %s." % (e.filename, e.strerror))
                continue

            path = l[self.index:]              # rm build directory path from the file full path
            dirName = os.path.dirname(path)    # install path
            fileName = os.path.basename(path)  # install file name
            if fileName.find(".") > 0:
                ext = "/*.*\n"                 # globbing for file names with extension
            else:
                ext = "/*\n"                   # globbing for file names without extension
            globName = dirName + ext           # use globbing for file names
            if globName not in self.items:     # append 'globbed' file name to the list 
                self.items.append(globName)

    def writeList(self):
        ''' create file that will be used by RPM build process
            File contents are files names one per line that will be included in RPM.
            Names use globbing that is expended by RPM
        '''
        f = open(self.fname, "w")
        for i in self.items:
            f.write(i)
        f.close

    def run(self):
        self.runCommand()
        self.writeList()

if __name__ == "__main__":
    app = Listing(sys.argv)
    app.run()
