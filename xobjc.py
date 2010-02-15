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

0.5 (2010-01-05)
- More refactoring
- Now work also when no properties are defined
- Prefix XPUBLIC also in Interface file to prepare for more intelligent
  handling of those marked methods in future
- Removed unsexy whitesapce 

0.6 (2010-01-06)
- Removed the prepending XPUBLIC from interface file because Interface
  Builder was not able to handle it  
- IBAction methods are always considered public (I don't see a case where
  they are not
- Static methods are also considered public

0.7 (2010-02-07)
- Fix for Apple Script calls
- Handle comment correctly
- NEw FORCE_METHODS setting 

0.8 (2010-0215)
- Moved @synthesize to the end of files
- Moved @property to the end of files

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

### CONFIG BEGIN 

BACKUP_FOLDER = 'BACKUP-XOBJC'

FORCE_METHODS = True

### CONFIG END 

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

rxViewDidUnload = re.compile("""
    \-\s*\(void\)\s*
        viewDidUnload
        \s*
        \{
        (?P<viewdidunloadbody> [^\}]*?)        
        \}
    """, re.VERBOSE | re.M | re.DOTALL)

rxViewDidUnloadBody = re.compile("""
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
        (XPUBLIC)?
    )     
    \s*
    (?P<name>
        [\-\+] 
        \s*    
        \([^\)]+\)
        \s*
        [a-zA-Z_]
        [^\{\=]+?
    ) 
    \{ 
        
""", re.VERBOSE | re.M | re.DOTALL)

rxInstance = re.compile("""
    XINSTANCE([^\s]+)
""", re.VERBOSE | re.M | re.DOTALL)

rxComment = re.compile("""
   (
    ^\s*\/\/.*?$
    |
    \/\*.*?\*\/
   )
""", re.VERBOSE | re.M | re.DOTALL)


class Module:
    
    def __init__(filename):
        self.base = filename[:filename.rfind(".")]
        self.h = self.base + '.h'
        self.m = self.baee = ".m"

def stripComments(value):
    return rxComment.sub('', value)

def extractVariables(data):
    return [x.strip() for x in data.strip().split(",")]

def insertString(base, pos, new):
    return base[:pos] + new + base[pos:]

def analyze(hdata, mdata):
    
    ### HEADER
        
    vars = dict()
    interfaceMatch = rxInterface.match(hdata)
    varblock = stripComments(interfaceMatch.group("varblock").strip())
    properties = interfaceMatch.group("properties")    
    
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
    body = implementationMatch.group("body")
    body = rxSynthesize.sub('', body).strip()
    block = "\n".join(block) + '\n\n'
            
    # Update 'dealloc'
    md = rxDealloc.search(body)
    if md:
        deallocbody = rxRelease.sub('', md.group("deallocbody")).strip()     
        if deallocbody:
            deallocbody = "    " + deallocbody + "\n\n"
        newdealloc = ("- (void)dealloc{ "
            + ("\n" + deallocbody).rstrip()
            + ("\n" + "\n".join(sorted(dealloc))).rstrip()
            + "\n    [super dealloc];\n}")
        body = rxDealloc.sub(newdealloc, body)
    else:
        newdealloc = "- (void)dealloc{\n" + "\n".join(sorted(dealloc)) + "\n    [super dealloc];\n}" 
        body += "\n\n" + newdealloc  

    # Update 'viewDidUnload' (iPhone only)
    md = rxViewDidUnload.search(body)
    if md:
        viewdidunloadbody = rxViewDidUnloadBody.sub('', md.group("viewdidunloadbody")).strip()     
        if viewdidunloadbody:
            viewdidunloadbody = "\n    " + viewdidunloadbody + "\n\n"
        newviewdidunloadbody = (
            "- (void)viewDidUnload{\n    [super viewDidUnload];\n" 
            + viewdidunloadbody 
            + "\n".join(sorted(viewdidunload)) 
            + "\n}")
        body = rxViewDidUnload.sub(newviewdidunloadbody, body)
          
    ### METHODS
    mDefs = []      
    xpub = 0  
    bodyStripped = stripComments(body)

    for mMethod in rxMethod.finditer(bodyStripped):
        mName = mMethod.group('name').strip()
        if (mMethod.group('kind') == 'XPUBLIC'):
            xpub += 1
            mDefs.append(mName + ';')
        elif mName.startswith("+") or mName.lstrip('-').lstrip().startswith("(IBAction)"):            
            mDefs.append(mName + ';')
    
    ### XINSTANCE
    mdi = rxInstance.search(bodyStripped)
    if mdi:
        xpub += 1
        mDefs.append("+ (id)instance;")
    
    # If no XPUBLIC was defined don't replace old stuff
    if mDefs or FORCE_METHODS:
        mDefs = "\n".join(sorted(mDefs)) + '\n\n'
    else:
        mDefs = properties       
          
    ### RESULT
   
    hdata = (hdata[:interfaceMatch.start("properties")] 
        + ('\n\n' + mDefs).rstrip()  
        + ('\n\n' + propBlock).rstrip()             
        + '\n\n' + hdata[interfaceMatch.end("properties"):])
        
    mdata = (mdata[:implementationMatch.start('body')] 
        + ('\n\n' + body).rstrip() 
        + ('\n\n' + block).rstrip() 
        + '\n\n' + mdata[implementationMatch.end('body'):]) 

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
    backupFolder = os.path.join(
        folder, 
        BACKUP_FOLDER, 
        'backup-' + datetime.datetime.today().strftime("%Y%m%d-%H%M%S"))
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
        # Bug workaround for SL, see http://kb2.adobe.com/cps/516/cpsid_51615.html
        import subprocess        
        subprocess.call(['arch', '-i386', 'osascript', '-e', 'activate application "Finder"'])
        subprocess.call(['arch', '-i386', 'osascript', '-e', 'activate application "XCode"'])

    else:
        if len(sys.argv) != 2:
            print "Usage: xobjc.py [filename]"
        else:
            modifyFiles(sys.argv[1])
