#!/usr/bin/env python

"""
TODO:

- ATOMIC
- ViewDidUnload
- Readonly
- Work without defined dealloc or more individual dealloc
- Work with more implementations etc. in one file and match name
- Create properties and synthesize in order the are defined in var block

"""

import re
import os
import os.path
import shutil
import pprint
import datetime

rxh = re.compile("""
.*?
@interface .*? 
\{ 
(?P<varblock> .*?)
\}
(?P<properties> .*?)
@end
.*?
""", re.VERBOSE|re.M|re.DOTALL)

rxm = re.compile("""
.*?
\@implementation\s+[a-zA-Z0-9_]+
(?P<body> .*)
(?P<dealloc> 
    \-\s*\(void\)\s*
    dealloc
    \s*
    \{
    .*?
    \[\s*super\s+dealloc\s*\]\s*\;\s*
    \}
)
""", re.VERBOSE|re.M|re.DOTALL)

rxvars = re.compile("""
    (XCOPY | XASSIGN | XRETAIN | XATOMIC | XREADONLY | XIBOUTLET | IBOutlet)
    \s+
    ([a-zA-Z0-9_][a-zA-Z0-9_\<\>]*)
    \s+
    ((        
        \*?
        \s*
        [a-zA-Z0-9_]+
        \s*
        \,?            
        \s*
    )+)
    \;
""", re.VERBOSE|re.M|re.DOTALL)

rxproperties = re.compile("""
    \@property  
    
    \s*
    
    (
        \( 
        \s*
        (copy | assign | retain | atomic | nonatomic)
        \s*
        \,?
        \s*
        (copy | assign | retain | atomic | nonatomic)?
        \s*
        \)
    )?
    
    \s*
    
    ([a-zA-Z0-9_][a-zA-Z0-9_\<\>]*)
    
    \s+
    
    ((        
        \*?
        \s*
        [a-zA-Z0-9_]+
        \s*
        \,?            
        \s*
    )+)
    \;
    
""", re.VERBOSE|re.M|re.DOTALL)

rxsyn =  re.compile("""
    \@synthesize
    \s+
    \w+       
    \s*
    \=?
    \s*
    \w*
    \;    
""", re.VERBOSE|re.M|re.DOTALL)

class Module:
    
    def __init__(filename):
        self.base = filename[:filename.rfind(".")]
        self.h = self.base + '.h'
        self.m = self.baee = ".m"

def extractVariables(data):
    return [x.strip() for x in data.strip().split(",")]

def insertString(base, pos, new):
    return base[:pos] + new + base[pos:]

def analyze(hdata, mdata):
    
    # HEADER
    
    vars = dict()
    m = rxh.match(hdata)
    varblock = m.group("varblock").strip()
    properties = m.group("properties")    
    if varblock and properties:
        
        # Analyze variable definitions
        # print repr(varblock.strip())        
        for mv in rxvars.finditer(varblock):                        
            mode, type_, names, names_ = mv.groups()
            # print mode, type_, extractVariables(names)
            for vname in extractVariables(names):
                vars[vname] = (mode.lower(), type_)    
        # pprint.pprint(vars)
                
        # Analyze property definitions
        if 0:
            print repr(properties.strip())
            for mp in rxproperties.finditer(properties):
                mode, mode1, mode2, type_, names, names_ = mp.groups()            
                for vname in extractVariables(names):
                    if vname in vars:
                        del vars[vname]
        else:
            properties = rxproperties.sub('', properties).lstrip()
                
        # Create missing properties
        # print
        # pprint.pprint(vars)
        block = []    
        for vname in sorted(vars.keys()):
            # print vname
            mode, type_ = vars[vname]
            if 1: #mode != 'iboutlet':   
                if vname.endswith('_'):
                    vname = vname[:-1]
                if mode == 'iboutlet':
                    mode = 'retain'
                elif mode == 'xiboutlet':
                    mode = "retain"
                    type_ = "IBOutlet %s" % type_
                else:
                    mode = mode[1:]                
                block.append("@property (nonatomic, %s) %s %s;" % (mode, type_, vname))
        block = "\n".join(block)        
        
        hdata = hdata[:m.start("properties")] + '\n\n' + block + '\n\n' + properties + hdata[m.end("properties"):]
        # print hdata
        
        # print "=" * 60
         
        # MODULE
    
        # print mdata
        m = rxm.match(mdata)    
        #print m.groups()
    
        dealloc = []       
        block = []    
    
        for vname in sorted(vars.keys()):
            # print vname
            mode, type_ = vars[vname]
            vname = vname.lstrip('*')
            if 1: # mode != 'iboutlet':  
                if vname.endswith('_'):
                    block.append("@synthesize %s = %s;" % ( vname[:-1], vname))
                else:
                    block.append("@synthesize %s;" % (vname))
            if mode not in ('xassign'):
                dealloc.append("    [%s release];" % vname)
                
        body = rxsyn.sub('',  m.group("body")).strip()
        block = '\n\n' + "\n".join(block) + '\n\n'
        dealloc = "\n\n- (void)dealloc{\n" + "\n".join(dealloc) + "\n    [super dealloc];\n}"    
    
        #print repr(m.group('dealloc'))
        mdata = mdata[:m.start('body')] + block + body + dealloc + mdata[m.end('dealloc'):]
        # print mdata
        
    return hdata, mdata

def modifyFiles(filename):
    # Calc filename
    base = os.path.normpath(os.path.abspath(filename))
    folder = os.path.dirname(base)
    filePart = os.path.basename(base)
    hfile = filename[:filename.rfind(".")] + '.h'
    mfile = filename[:filename.rfind(".")] + '.m'
    
    # Check files
    if not os.path.isfile(hfile):
        print "File %r does not exist" % hfile
        return
    if not os.path.isfile(mfile):
        print "File %r does not exist" % hfile
        return
    
    # Backup files
    backupFolder = os.path.join(folder, 'objc-backup-' + datetime.datetime.today().strftime("%Y%m%d-%H%M%S"))
    os.makedirs(backupFolder)
    shutil.copyfile(hfile, os.path.join(backupFolder, filePart[:-2] + '.h'))
    shutil.copyfile(mfile, os.path.join(backupFolder, filePart[:-2] + '.m'))
    print "Created backup of files in %r" % backupFolder

    # Convert
    hdata, mdata = analyze(
        open(hfile).read(), 
        open(mfile).read())    
    open(hfile, 'w').write(hdata)
    open(mfile, 'w').write(mdata)
    print "Modified %r" % hfile
    print "Modified %r" % mfile
    
if __name__=="__main__":
    import sys
    if len(sys.argv)!=2:
        print "Usage: objc.py [filename]"
    else:
        modifyFiles(sys.argv[1])
