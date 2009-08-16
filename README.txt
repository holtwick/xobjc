xobjc
=====

A tool for making annoying every day tasks for Objective-C developers, especially
iPhone developers, easier. Therefore this tool will help you writing semi-automatically
the @property and @synthesize stuff. It also updates the dealloc method to release
your objects. And you can define the attributes according to the Google Objective-C
styleguide using a trailing underscore, i.e. your public attribute is then defined 
without this underscore.

Preparation:

You have to define some helpers in your code that will indicate your properties

#define XASSIGN
#define XRETAIN 
#define XCOPY 
#define XATOMIC 
#define XREADONLY
#define XIBOUTLET

Your code:

In your header file mark you properties like this

@interface CountdownView : UIView {
    XIBOUTLET UILabel *_dd, *_hh, *_mm;
    XIBOUTLET UILabel *_matchTitle;

    id somewhat_;

    XCOPY NSString *title_;
    XASSIGN id delegate_;
    XRETAIN UIView *myNewView_;
}

@end

Usage:

$ python objc.py sample.h

After that your .h and .m files are updated. XCode should reload your code in the editor
automatically. The command also creates a new subfolder which contains a backup of your 
original code, hope you never will need it ;)