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

    #define XASSIGN
    #define XRETAIN 
    #define XCOPY 
    #define XATOMIC 
    #define XREADONLY
    #define XIBOUTLET

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
	    int age;
	}

	@end

In your module file you can mark public methods like this:

	XPUBLIC
	- (void)somePubMethod { /* ... */ }

Usage
-----

``$ python xobjc.py sample.h``

After that your ``.h`` and ``.m`` files are updated. XCode should reload your code in the editor
automatically. The command also creates a new subfolder which contains a backup of your 
original code, hope you never will need it ;)

Example
-------

Some pictures say more than thousand words. Here is a before/after diff showing the magic:

![Header](http://mail.holtwick.it/xobjc/demo-h.PNG "Header")

![Module](http://mail.holtwick.it/xobjc/demo-m.PNG "Module")

XCode Integration
-----------------

In Xcode in the menu choose the script symbol and there ``Edit User Scripts``. Create a new
entry and copy and paste the contents of the file ``xobjc.py`` into the text field. That's all, 
you are done. Just call the script form the menu or via the key shortcut you defined while you
are in the header or implementation file you like to become updated.

Related
-------

 * <http://cocoawithlove.com/2008/12/instance-variable-to-synthesized.html>
 * <http://allancraig.net/blog/?p=315> 
 * <http://github.com/wookay/da/blob/b1190cd83df5700b0b6035eef2959c7968bde488/ruby/xcode/property_automation.rb>

Known Bugs and Problems
-----------------------

 * With Snow Leopard MacOS X 10.6 the 'osascript' helper, which is used for XCode integration, might throw some
   errors. Just ignore it until it is solved by Adobe or Apple, it does not affect xobjc. 
   Here is a related discussion on the problem http://forums.adobe.com/message/2225116
