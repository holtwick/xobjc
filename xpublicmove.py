"""
Transforms:

XPUBLIC
- (void)bla {

Into:

- (XPUBLIC void)bla {

For Xcode 4.3 compatibility
"""

import glob
import re

rx = re.compile("\-\s*\(")
files = (
    # Add you implementation files here
    # glob.glob("/Users/SOMEUSER/work/SOMETPATH/*.m")
    )

for name in files:
    print name
    next = 0 
    lines = []
    for line in open(name, "r").readlines():
        if line.startswith("XPUBLIC"):
            next = 1
            continue
            # print line
        if next and line.startswith("-"):
            line = rx.sub("- (XPUBLIC ", line)
            print "   ", line,
        lines += line.rstrip() + '\n'
        next = 0;

    open(name, "w").writelines(lines)
