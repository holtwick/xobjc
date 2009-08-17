#import <UIKit/UIKit.h>

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
