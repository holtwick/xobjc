xobjc
=====

[![Flattr this git repo](http://api.flattr.com/button/flattr-badge-large.png)](https://flattr.com/submit/auto?user_id=holtwick&url=https://github.com/holtwick/xobjc&title=xobjc&language=en_GB&tags=github&category=software)

**FULL XCODE4 COMPATIBILITY***

**Xcode4 Demo on YouTube [youtube.com/watch?v=Mzfv-ANydW4](http://www.youtube.com/watch?v=Mzfv-ANydW4).**

**XCode3 Demo on mov.io [mov.io/fE](http://mov.io/fE).**

<div>
	<iframe src='http://mov.io/go/showvideo/player/fE?autoplay=false' width='430' height='391' scrolling='no' frameborder='0'></iframe>
</div>
	
A tool for making annoying every day tasks for Objective-C developers, especially
iPhone developers, easier. Therefore this tool will help you writing semi-automatically
the ``@property`` and ``@synthesize`` stuff. It also updates the ``dealloc`` method to release
your objects. And you can define the attributes according to the 
[Google Objective-C Styleguide](http://google-styleguide.googlecode.com/svn/trunk/objcguide.xml#Variable_Name) 
using a trailing underscore, i.e. your public attribute is then defined 
without this underscore. But also a leading underscore is ok. Public method can easily be defined by
prepending XPUBLIC in the implementation part.

No more redundancies and nonsense typing orgies! You'll save a lot of time!

Preparations
------------

You have to define some helpers in your code that will indicate your properties 
(you can alternatively use ``xobjc.h`` from this package):

    #define XRETAIN 
    #define XIBOUTLET
    #define XASSIGN
    #define XCOPY 
    #define XPROPERTY(...)
    #define XNIL nil
    #define XPUBLIC 

Your code
---------

In your header file mark you properties like this:

	#import <UIKit/UIKit.h>
	#import "xobjc.h"

	@interface DemoViewController : UIViewController {
	    XIBOUTLET UILabel *header_;
	    XIBOUTLET UITextView *message_;    
	    XASSIGN id delegate_;    
	    XASSIGN int counter;    
	    XRETAIN NSArray *listOfUsers_;    
	    XCOPY NSString *secretKey_;
        XPROPERTY(readonly) BOOL isPublic_; 
	    int age;
	}

	@end

In your module file you can mark public methods like this:

	XPUBLIC
	- (void)somePubMethod { /* ... */ }
    
(IBAction, class initializers and class methods are always considered public)

Usage
-----

``$ python xobjc.py sample.h``

After that your ``.h`` and ``.m`` files are updated. XCode should reload your code in the editor
automatically. The command also creates a new subfolder which contains a backup of your 
original code, hope you never will need it ;)

Example
-------

Some pictures say more than thousand words. Here is a before/after diff showing the magic:

![Header](https://github.com/holtwick/xobjc/raw/master/website/demo-h.png "Header")

![Module](https://github.com/holtwick/xobjc/raw/master/website/demo-m.png "Module")

XCode4 Integration
------------------

Edit your projects 'Scheme' and add a new 'Run Script Action' to your 'Build / Pre-actions'. 
Fill in the full path of your xobjc4.py. Now each time you build your project this script
will be run. This is super handy.

![Header](https://github.com/holtwick/xobjc/raw/master/website/xcode4scheme.png "Xcode4 Scheme Modifications")

If Growl is installed it will also issue a notification.


XCode3 Integration
------------------

In Xcode in the menu choose the script symbol and there ``Edit User Scripts``. Create a new
entry and copy and paste the contents of the file ``xobjc.py`` into the text field. That's all, 
you are done. Just call the script form the menu or via the key shortcut you defined while you
are in the header or implementation file you like to become updated.

Related
-------

Macro extensions for XCode

 * [xcode-text-macros](http://github.com/liyanage/xcode-text-macros) 

Similar approaches and discussions

 * <http://cocoawithlove.com/2008/12/instance-variable-to-synthesized.html>
 * <http://allancraig.net/blog/?p=315> 
 * <http://github.com/wookay/da/blob/b1190cd83df5700b0b6035eef2959c7968bde488/ruby/xcode/property_automation.rb>

Known Bugs and Problems
-----------------------

 * With Snow Leopard MacOS X 10.6 the 'osascript' helper, which is used for XCode integration, threw some
   errors. I used a workaround I found here to circumvent the problem: http://kb2.adobe.com/cps/516/cpsid_51615.html
   If you are using non Intel architecture or other OS you might need to modify this portion of code in xobjc.py

License (MIT License)
---------------------

Copyright (c) 2011 Dirk Holtwick

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

