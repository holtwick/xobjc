/*
 
 Apply `xobjc` to this file to see the effect 
 
 */

#import <UIKit/UIKit.h>
#import "xobjc.h"

@interface DemoViewController : UIViewController {
    XIBOUTLET UILabel *header_;
    XIBOUTLET UITextView *message_;    
    XASSIGN id _delegate;    
    XASSIGN int counter;    
    XRETAIN NSArray *listOfUsers_;    
    XCOPY NSString *secretKey_;
    int age;
}

@end
