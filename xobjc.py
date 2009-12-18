#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Copyright (c) 2009 Dirk Holtwick <http://www.holtwick.it>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

CHANGELOG:

0.1 
- Initial release

0.2 (2009-09-04)
- Dealloc can contain custom data
- Adds missing dealloc correctly

0.3 (2009-09-11)
- viewDidUnload support

0.4 (2009-12-18)
- Joined with version of 'freewizard' with leading underscore support
- Some refactoring to make the source more readable
- Added XPUBLIC to mark public methods
- Alphabetical sorting of blocks
- Added MIT license

TODO:

- ATOMIC
- Readonly
- Work with more implementations etc. in one file and match name
- NSCoder support
- XPRIVATE
"""

import re
import os
import os.path
import shutil
import pprint
import datetime

rxInterface = re.compile("""
    .*?
    @interface .*? 
    \{ 
    (?P<varblock> .*?)
    \}
    (?P<properties> .*?)
    @end
    .*?
    """, re.VERBOSE | re.M | re.DOTALL)

rxImplementation = re.compile("""
    .*?
    \@implementation\s+(?P<name>[a-zA-Z0-9_]+)
    (?P<body> .*?)
    \@end
    """, re.VERBOSE | re.M | re.DOTALL)

rxDealloc = re.compile("""
    \-\s*\(void\)\s*
        dealloc
        \s*
        \{
        (?P<deallocbody> .*?)    
        \[\s*super\s+dealloc\s*\]\s*\;\s*
        \}
    """, re.VERBOSE | re.M | re.DOTALL)

rxRelease = re.compile("""
    \[\s*[^\s]+\s+release\s*\]\s*\;\s*$
    """, re.VERBOSE | re.M | re.DOTALL)

rxviewdidunload = re.compile("""
    \-\s*\(void\)\s*
        viewDidUnload
        \s*
        \{
        (?P<viewdidunloadbody> [^\}]*?)        
        \}
    """, re.VERBOSE | re.M | re.DOTALL)

rxViewDidUnload = re.compile("""
    \[\s*super\s+viewDidUnload\s*\]\s*\;
    |
    self\.[a-zA-Z0-9_]+ \s* \= \s* XNIL \s* \;
    """, re.VERBOSE | re.M | re.DOTALL)

rxVariables = re.compile("""
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
    """, re.VERBOSE | re.M | re.DOTALL)

rxProperty = re.compile("""
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
    
""", re.VERBOSE | re.M | re.DOTALL)

rxSynthesize = re.compile("""
    \@synthesize
    \s+
    \w+       
    \s*
    \=?
    \s*
    \w*
    \;    
    """, re.VERBOSE | re.M | re.DOTALL)

rxLeadingUnderscore = re.compile("(\s*\*?\s*)_(.+)")

rxMethod = re.compile("""
    (?P<kind>
        XPUBLIC
    )     
    \s*
    (?P<name>
        [\-\+] 
        \s*    
        .+?
    ) 
    \s*        
    \{ 
        
""", re.VERBOSE | re.M | re.DOTALL)

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
    
    ### HEADER
        
    vars = dict()
    interfaceMatch = rxInterface.match(hdata)
    varblock = interfaceMatch.group("varblock").strip()
    properties = interfaceMatch.group("properties")    
    if varblock and properties:
        
        # Collect variable definitions
        for mv in rxVariables.finditer(varblock):                        
            mode, type_, names, names_ = mv.groups()
            for vname in extractVariables(names):
                vars[vname] = (mode.lower(), type_)    
        
        # Remove @properties completely        
        properties = rxProperty.sub('', properties).lstrip()
                
        # Create missing @properties
        propBlock = []    
        for vname in sorted(vars.keys(), key=lambda k:k.strip('*').strip('_')):
            mode, type_ = vars[vname]
            vnamem = rxLeadingUnderscore.match(vname)
            if vname.endswith('_'):
                vname = vname[:-1]
            elif vnamem:
                vname = vnamem.group(1) + vnamem.group(2)
            if mode == 'iboutlet':
                mode = 'retain'
            elif mode == 'xiboutlet':
                mode = "retain"
                type_ = "IBOutlet %s" % type_
            else:
                mode = mode[1:]                
            propBlock.append("@property (nonatomic, %s) %s %s;" % (mode, type_, vname))
        propBlock = "\n".join(propBlock)        
                 
                 
        ### MODULE

        # Find implementation blinterfaceMatch       
        implementationMatch = rxImplementation.match(mdata)    
        impName = implementationMatch.group('name')
        
        viewdidunload = []
        dealloc = []       
        block = []    
    
        # Create @synthesize block
        for vname in sorted(vars.keys(), key=lambda k:k.strip('*').strip('_')):
            # print vname
            mode, type_ = vars[vname]
            vname = vname.lstrip('*')
            pvname = vname
            if vname.endswith('_'):
                pvname = vname[:-1]
                block.append("@synthesize %s = %s;" % (pvname, vname))
            elif vname.startswith('_'):
                pvname = vname[1:]
                block.append("@synthesize %s = %s;" % (pvname, vname))
            else:
                block.append("@synthesize %s;" % (vname))
            if mode not in ('xassign'):
                dealloc.append("    [%s release];" % vname)
            if mode.endswith('iboutlet'):
                viewdidunload.append("    self.%s = XNIL;" % pvname)
        
        # Replace @synthesize block 
        body = rxSynthesize.sub('', implementationMatch.group("body")).strip()
        block = '\n\n' + "\n".join(block) + '\n\n'
                
        # Update 'dealloc'
        md = rxDealloc.search(body)
        if md:
            deallocbody = rxRelease.sub('', md.group("deallocbody")).strip()     
            if deallocbody:
                deallocbody = "    " + deallocbody + "\n\n"
            newdealloc = "- (void)dealloc{\n" + deallocbody + "\n".join(sorted(dealloc)) + "\n    [super dealloc];\n}"
            body = rxDealloc.sub(newdealloc, body)
        else:
            newdealloc = "- (void)dealloc{\n" + "\n".join(sorted(dealloc)) + "\n    [super dealloc];\n}" 
            body += "\n\n" + newdealloc  

        # Update 'viewDidUnload' (iPhone only)
        md = rxviewdidunload.search(body)
        if md:
            viewdidunloadbody = rxViewDidUnload.sub('', md.group("viewdidunloadbody")).strip()     
            if viewdidunloadbody:
                viewdidunloadbody = "\n    " + viewdidunloadbody + "\n\n"
            newviewdidunloadbody = "- (void)viewDidUnload{\n    [super viewDidUnload];\n" + viewdidunloadbody + "\n".join(sorted(viewdidunload)) + "\n}" 
            body = rxviewdidunload.sub(newviewdidunloadbody, body)
              
        ### METHODS
        mDefs = []
        for mMethod in rxMethod.finditer(body):
             if mMethod.group('kind') == 'XPUBLIC':
                 mDefs.append(mMethod.group('name') + ';')
        
        # If no XPUBLIC was defined don't replace old stuff
        if mDefs:
            mDefs = "\n".join(sorted(mDefs)) + '\n\n'
        else:
            mDefs = properties       
              
        ### RESULT
       
        hdata = hdata[:interfaceMatch.start("properties")] + '\n\n' + propBlock + '\n\n' + mDefs + hdata[interfaceMatch.end("properties"):]
        mdata = mdata[:implementationMatch.start('body')] + block + body + '\n\n' + mdata[implementationMatch.end('body'):] 

    return hdata, mdata

def modifyFiles(filename):
    
    # Calculate basic filenames
    base = os.path.normpath(os.path.abspath(filename))
    folder = os.path.dirname(base)
    filePart = os.path.basename(base)
    hfile = filename[:filename.rfind(".")] + '.h'
    mfile = filename[:filename.rfind(".")] + '.m'
    
    # Check if files exist
    if not os.path.isfile(hfile):
        print "File %r does not exist" % hfile
        return
    if not os.path.isfile(mfile):
        print "File %r does not exist" % hfile
        return
    
    # Backup files
    backupFolder = os.path.join(folder, '.xobjc-backup', 'backup-' + datetime.datetime.today().strftime("%Y%m%d-%H%M%S"))
    os.makedirs(backupFolder)
    shutil.copyfile(hfile, os.path.join(backupFolder, filePart[:-2] + '.h'))
    shutil.copyfile(mfile, os.path.join(backupFolder, filePart[:-2] + '.m'))
    print "Created backup of files in %r" % backupFolder

    # Handle and modify files
    hdata, mdata = analyze(
        open(hfile).read(),
        open(mfile).read())    
    open(hfile, 'w').write(hdata)
    open(mfile, 'w').write(mdata)
    print "Modified %r" % hfile
    print "Modified %r" % mfile
    
if __name__ == "__main__":
    import sys
        
    # You can also place it into 'XCode User Scripts' but it does not relead the window yet
    try:
        filename = '%%%{PBXFilePath}%%%'
    except:
        filename = ''
    
    if filename and (not filename.startswith('%')):
        modifyFiles(filename)

        # Trick to reload files in XCode
        import subprocess        
        subprocess.call(['osascript', '-e', 'activate application "Finder"'])
        subprocess.call(['osascript', '-e', 'activate application "XCode"'])

    else:
        if len(sys.argv) != 2:
            print "Usage: xobjc.py [filename]"
        else:
            modifyFiles(sys.argv[1])
