#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Copyright (c) 2009-2012 Dirk Holtwick <http://www.holtwick.it>

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
- New FORCE_METHODS setting 

0.8 (2010-02-15)
- Moved @synthesize to the end of files
- Moved @property to the end of files

0.9 (2010-03-14)
- Methods which start with 'initWith' are considered public
- Added XPROPERTY(..) for individual property definitions, e.g.
  XPROPERTY(readonly) id test;
- Removed XATOMIC and XREADONLY
- Code cleanup

0.10
- Now also works as build script
- Only handle files if different file times
- Only change files that contain X... macros
- Nonatomic can be turned of as default
- Strip trailing spaces
- Multiple file and path arguments
- Added XDELEGATE

0.11 (2010-09-07)
- Fix: Can handle missing spaces around asterisk
- External settings did not work, therefore removed

0.12 (2010-09-21)
- Categories support
- Expand environment variables for backup path
- Support for .mm file suffixes
- DEBUG does not write files

0.13 (2011-01-08)
- XPROPERTY arguments case sensitive
- Added 'xobjc' marker into @property
- 'XASSIGN BOOL xxx' creates corect 'isXxx' getter

0.14 (2012-02-23)
- Xcode 4.3 is picky about the position of XPUBLIC therefore
  moved it into the return parameter definition like
  - (XPUBLIC void)someMethod
- Empty deallocs will not be written

TODO:

- Work with more implementations etc. in one file and match name
  => Currently just one implementation per file
- NSCoder support 
  => Create all needed stuff
- XPRIVATE 
  => Put them into a category in the implementation file

"""

__version__ = "0.14"

import re
import os
import os.path
import shutil
import pprint
import datetime
import subprocess

### CONFIG BEGIN 

# !!! PLEASE CHANGE THE FOLLOWING TO YOU NEEDS !!!

# No backup at all
# BACKUP_FOLDER = None

# Subfolder of the sources location
# BACKUP_FOLDER = 'BACKUP-XOBJC'

# All into one absolute path
BACKUP_FOLDER = os.path.expandvars('${HOME}/work/_build/__xobjc_backup')
DEBUG = 0
FORCE_METHODS = False #True
BOOL_WITH_IS_GETTER = True
STRIP_TRAILING_SPACES = True
# NONATOMIC = ""
NONATOMIC = "nonatomic, "

### CONFIG END 

rxInterface = re.compile("""
    .*?
    @interface (?P<interface> .*?) 
     \{
    (?P<varblock> .*? )
    \}
    (?P<properties> .*?)
    @end
    .*?
    """, re.VERBOSE | re.M | re.DOTALL)

rxInterfaceCat = re.compile("""
    .*?
    @interface 
        (?P<interface> .*?) 
        \( 
            (?P<category> .*?)
        \) 
        
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
        (\[\s*[^\s]+\s+x?release\s*\]\s*\;\s*)*
        \[\s*super\s+dealloc\s*\]\s*\;\s*
        \}
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
    self\.[a-zA-Z0-9_]+ \s* \= \s* (xnil|XNIL) \s* \;
    """, re.VERBOSE | re.M | re.DOTALL)

rxVariables = re.compile("""
    (XCOPY | XASSIGN | XRETAIN  | XIBOUTLET | XDELEGATE | XPROPERTY\(.*?\))
    \s+
    ([^\s]*)
    ((        
        (?:
          \s*\* 
          | 
          \s
        )
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
        .*?
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

#rxInstance = re.compile("""
#    XINSTANCE([^\s]+)
#""", re.VERBOSE | re.M | re.DOTALL)

rxComment = re.compile("""
    (
        \/\*.*?\*\/
        |
        ^\s*\/\/.*?$
    )
""", re.VERBOSE | re.M | re.DOTALL)

rxInitMethod = re.compile("""
    \-\s*(.*?)\s*initWith.*
""", re.VERBOSE | re.M | re.DOTALL)

def mySorted(v, **k):
    return v
    # return sorted(v, **k)

class Module:
    
    def __init__(filename):
        self.base = filename[:filename.rfind(".")]
        self.h = self.base + '.h'
        self.m = self.baee = ".m"

def stripComments(value):
    #if DEBUG: 
    #    for c in rxComment.findall(value): 
    #        print c
    return rxComment.sub('', value)

def extractVariables(data):
    return [x.strip() for x in data.strip().split(",")]

def insertString(base, pos, new):
    return base[:pos] + new + base[pos:]

def analyze(hdata, mdata):
    
    ### HEADER
        
    vars = dict()
    
    propBlock = []    
    viewdidunload = []
    dealloc = []       
    block = []   
    isCategory = 0
    
    interfaceMatch = rxInterface.match(hdata) 
    if not interfaceMatch:
        interfaceMatch = rxInterfaceCat.match(hdata)  
        if not interfaceMatch:  
            return None, None
        else:
            isCategory = 1
    
    if not isCategory:
        varblock = interfaceMatch.group("varblock")    
        varblock = stripComments(varblock.strip())
    
        # Collect variable definitions
        for mv in rxVariables.finditer(varblock):                        
            mode, type_, names, names_ = mv.groups()
            for vname in extractVariables(names):
                vars[''.join(vname.split())] = (mode.lower(), type_, mode)    
    
    # Remove @properties completely from interface 
    properties = interfaceMatch.group("properties")    
    
    if isCategory:
        for mpp in rxProperty.finditer(properties):   
            propBlock.append(mpp.group(0))                     
                    
    if not isCategory:
        properties = rxProperty.sub('', properties).lstrip()
        
        # Create @properties
        for vname in mySorted(vars.keys(), key=lambda k:k.strip('*').strip('_')):
            mode, type_, origMode = vars[vname]
        
            iboutlet = 0
            star = '*' if vname.startswith('*') else ''
            name = vname.lstrip('*') # Withoout leading *
            pvname = name # Without underscore
        
            # Google compatible synthesize
            if name.endswith('_'):
                pvname = name[:-1]
                block.append("@synthesize %s = %s;" % (pvname, name))
            elif name.startswith('_'):
                pvname = name[1:]
                block.append("@synthesize %s = %s;" % (pvname, name))
            else:
                block.append("@synthesize %s;" % (name))
            
            # Properties
            propMarker = "xobjc "
            if mode == 'xiboutlet':
                iboutlet = 1
                mode = "retain"
                type_ = "IBOutlet %s" % type_
                propBlock.append("@property (%s%s%s) %s %s%s;" % (propMarker, NONATOMIC, mode, type_, star, pvname))
            elif mode == 'xdelegate':
                iboutlet = 1
                mode = "assign"
                type_ = "IBOutlet %s" % type_
                propBlock.append("@property (%s%s%s) %s %s%s;" % (propMarker, NONATOMIC, mode, type_, star, pvname))
            elif mode.startswith('xproperty('):
                # XXX Iboutlet
                pattr = origMode.strip()[10:-1]
                propBlock.append("@property (%s%s) %s %s%s;" % (propMarker, pattr, type_, star, pvname))
                mode = 'assign'
                pattrlist = [x.strip().lower() for x in pattr.split(',')]
                if 'retain' in pattrlist or 'copy' in pattrlist:
                    mode = 'retain'
            else:
                mode = mode[1:]
                if BOOL_WITH_IS_GETTER and type_ == "BOOL":
                    mode = "getter=is%s%s" % (pvname[0].capitalize(), pvname[1:])
                propBlock.append("@property (%s%s%s) %s %s%s;" % (propMarker, NONATOMIC, mode, type_, star, pvname))
        
            # print mode 
        
            # Release stuff
            if mode in ('retain', 'copy'):
                dealloc.append("    [%s xrelease];" % name)

            if iboutlet:
                viewdidunload.append("    self.%s = xnil;" % pvname)

        # print viewdidunload
    
    propBlock = "\n".join(propBlock)        
             
    ### MODULE

    # Find implementation blinterfaceMatch       
    implementationMatch = rxImplementation.match(mdata)    
    impName = implementationMatch.group('name')
        
    #if DEBUG and implementationMatch:
    #    print "Implementation", implementationMatch.groups()
        
    # Replace @synthesize block 
    body = implementationMatch.group("body")

    if not isCategory:    
        body = rxSynthesize.sub('', body).strip()
        block = "\n".join(block) + '\n\n'
            
        # Update 'dealloc'
        md = rxDealloc.search(body)
        if md:
            deallocbody = md.group("deallocbody").strip()     
            if deallocbody or dealloc:
                # deallocbody = rxRelease.sub('', md.group("deallocbody")).strip()     
                if deallocbody:
                    deallocbody = "    " + deallocbody + "\n\n"
                newdealloc = ("- (void)dealloc { "
                    + ("\n" + deallocbody).rstrip()
                    + ("\n" + "\n".join(mySorted(dealloc))).rstrip()
                    + "\n    [super dealloc];\n}")
                body = rxDealloc.sub(newdealloc, body)
        else:
            if dealloc:
                newdealloc = "- (void)dealloc {\n" + "\n".join(mySorted(dealloc)) + "\n    [super dealloc];\n}" 
                body += "\n\n" + newdealloc  

        # Update 'viewDidUnload' (iPhone and iPad only)
        md = rxViewDidUnload.search(body)
        if md:
            viewdidunloadbody = rxViewDidUnloadBody.sub('', md.group("viewdidunloadbody")).strip()     
            if viewdidunloadbody:
                viewdidunloadbody = "\n    " + viewdidunloadbody + "\n\n"
            newviewdidunloadbody = (
                "- (void)viewDidUnload {\n    [super viewDidUnload];\n" 
                + ("    " + viewdidunloadbody.strip()).rstrip() 
                + ("\n" + "\n".join(mySorted(viewdidunload))).rstrip() 
                + "\n}")
            body = rxViewDidUnload.sub(newviewdidunloadbody, body)
          
    ### METHODS
    mDefs = []      
    xpub = 0  
    bodyStripped = stripComments(body)

    for mMethod in rxMethod.finditer(bodyStripped):
        mName = mMethod.group('name').strip()
        # if mMethod.group("comment"):
        #    mName = "\n" + mMethod.group("comment").strip() + "\n" + mName
        #if DEBUG: 
        
        print mName, mMethod.groups()
        if (mMethod.group('kind') == 'XPUBLIC'):
            xpub += 1
            mDefs.append(mName + ';')
        elif mName.startswith("+") or mName.lstrip('-').lstrip().startswith("(IBAction)"):            
            mDefs.append(mName + ';')
        elif mName.lstrip('-').lstrip().startswith("(XPUBLIC "):            
            mDefs.append(mName.replace("XPUBLIC ", "") + ';')
            xpub += 1
        elif rxInitMethod.match(mName):
            mDefs.append(mName + ';')        
    
    ### XINSTANCE
    #mdi = rxInstance.search(bodyStripped)
    #if mdi:
    #    xpub += 1
    #    mDefs.append("+ (id)instance;")
    
    # If no XPUBLIC was defined don't replace old stuff
    if mDefs or FORCE_METHODS:
        # mDefs = "\n".join(mySorted(mDefs)) + '\n\n'
        mDefs = "\n".join(mDefs) + '\n\n'
    else:
        mDefs = properties       
          
    ### RESULT
   
    if isCategory:

        hdata = (hdata[:interfaceMatch.start("properties")] 
            + ('\n\n' + propBlock).rstrip()             
            + ('\n\n' + mDefs).rstrip()  
            + '\n\n' + hdata[interfaceMatch.end("properties"):])
                
    else:
        
        hdata = (hdata[:interfaceMatch.start("properties")] 
            + ('\n\n' + mDefs).rstrip()  
            + ('\n\n' + propBlock).rstrip()             
            + '\n\n' + hdata[interfaceMatch.end("properties"):])
        
        mdata = (mdata[:implementationMatch.start('body')] 
            + ('\n\n' + body).rstrip() 
            + ('\n\n' + block).rstrip() 
            + '\n\n' + mdata[implementationMatch.end('body'):]) 

    # Did something change?
    if xpub or propBlock:
        return hdata, mdata
        
    return None, None

def modifyFiles(filename):
    
    # Calculate basic filenames
    base = os.path.normpath(os.path.abspath(filename))
    folder = os.path.dirname(base)
    filePart = os.path.basename(base)
    
    if filePart == "main.m":
        # print "File %r will not be modified" % filePart
        return False
        
    hfile = filename[:filename.rfind(".")] + '.h'
    mfile = filename[:filename.rfind(".")] + '.m'
    
    # Check if files exist
    if not os.path.isfile(hfile):
        # print "File %r does not exist" % hfile
        return False
    if not os.path.isfile(mfile):
        # print "File %r does not exist" % hfile
        mfile = filename[:filename.rfind(".")] + '.mm'
        if not os.path.isfile(mfile):
            return False
    
    htime = os.stat(hfile).st_mtime
    mtime = os.stat(mfile).st_mtime
    
    if htime == mtime:
        # print "No update needed"
        return False

    # Handle and modify files
    hsrc = open(hfile).read()
    msrc = open(mfile).read()
    if ("noxobjc" in hsrc.lower()) or ("noxobjc" in msrc.lower()):
        # print "File ignored"
        return False

    # Handle and modify files    
    hdata, mdata = analyze(
        hsrc,
        msrc)   
             
    if not (hdata and mdata):
        return False
        
    # Backup files
    if BACKUP_FOLDER:
        backupFolder = os.path.join(
            folder, 
            BACKUP_FOLDER, 
            'backup-' + datetime.datetime.today().strftime("%Y%m%d-%H%M%S"))
        if not os.path.isdir(backupFolder):
            os.makedirs(backupFolder)
        shutil.copyfile(hfile, os.path.join(backupFolder, filePart[:-2] + '.h'))
        shutil.copyfile(mfile, os.path.join(backupFolder, filePart[:-2] + '.m'))
        # print "Created backup of files in %r" % backupFolder


    if STRIP_TRAILING_SPACES:
        hdata = "\n".join([l.rstrip() for l in hdata.splitlines()])
        mdata = "\n".join([l.rstrip() for l in mdata.splitlines()])
    
    if DEBUG:        
        print "=" * 80
        print hfile
        print "=" * 80
        print hdata
        print "=" * 80
        print mfile
        print "=" * 80
        print mdata
    
    if not DEBUG:
        f = open(hfile, 'w')
        f.write(hdata)
        f.close()
    
        f = open(mfile, 'w')
        f.write(mdata)
        f.close()
    
        # Same file time
        subprocess.call(['touch', hfile, mfile])
    
    #print "Modified %r" % hfile
    #print "Modified %r" % mfile
    
    return True
    
def xcodeReload():
    # Trick to reload files in XCode
    # Bug workaround for SL, see http://kb2.adobe.com/cps/516/cpsid_51615.html    
    # print "XCode refresh"        
    # subprocess.call(['arch', '-i386', 'osascript', '-e', 'activate application "Finder"\nactivate application "XCode"'])
    pass

def callAppleScript(script, input=None):
    import StringIO
    if not input:
        return subprocess.check_output(
            ['osascript', '-e', script],
            stderr=subprocess.STDOUT)
            
    p = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    p.stdin.write(input)
    ret = p.communicate()[0]
    p.stdin.close()
    return ret

def callGrowl(msg):
    callAppleScript("""
        tell application "GrowlHelperApp"
        	set the allNotificationsList to {"XObjC"}
        	set the enabledNotificationsList to {"XObjC"}
        	register as application "XObjC" all notifications allNotificationsList default notifications enabledNotificationsList icon of application "XCode"
        	notify with name "XObjC" title "XCode" description "%s" application name "XObjC"
        end tell
        """ % repr(msg)[1:-1])

OUT = []

def out(*a):
    OUT.append(" ".join([str(v) for v in a]))
    
def main():
    filenames = callAppleScript("""
        tell application id "com.apple.dt.Xcode"
            return path of source documents
        end tell
        """)
        
    if not filenames:
        print "Nothing to do"
    
    filenames = [n.strip() for n in filenames.split(',')]
    
    modified = False
    for filename in filenames: 
    
        filename = os.path.abspath(filename)
        # print "Analyze %s" % filename
        
        mfiles = [filename] 
        
        # XXX Obsolete?
        if os.path.isdir(filename):            
            for root, dirs, files in os.walk(filename):
                for name in files:
                    if (BACKUP_FOLDER not in root) and name.endswith(".m"):                        
                        mfiles.append(os.path.join(root, name))
    
        # print "FILES:"
        # print "\n".join(mfiles)
        
        # elif srcroot:
        #   files = glob.glob("Classes/*.m")

        if mfiles:
           
            for fn in mfiles:
                if modifyFiles(fn):
                    out("Modified: %s" % os.path.basename(fn))
                    modified = True
    
    if modified:
        # xcodeReload()
        pass
    else:
        out("No modifications needed")
    
    s = '\n'.join(OUT)
    if s:
        print s
        callGrowl(s)
    
if __name__ == "__main__":
    main()
