xobjc
=====

**See the introduction video here [mov.io/fE](http://mov.io/fE).**

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

XCode3 Integration
------------------

In Xcode in the menu choose the script symbol and there ``Edit User Scripts``. Create a new
entry and copy and paste the contents of the file ``xobjc.py`` into the text field. That's all, 
you are done. Just call the script form the menu or via the key shortcut you defined while you
are in the header or implementation file you like to become updated.

XCode4 Integration
------------------

Copy `XObjC Tool.workflow` to `~/Library/Services/`. Now edit the workflow with `Automator` and
adjust the path to `xobjc4.py`. You can now add a keyboard shortcut to it via the Keyboard settings
in the System Preferences tool. In XCode4 you can call it via the `Services` menu or via your keyboard shortcut.

Known Bugs: It does only work for the first tab. If someone can help out with a modification of the 
AppleScript this would be very appreciated. Thanks.

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
