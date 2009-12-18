#import <UIKit/UIKit.h>

@interface DemoViewController : UIViewController {
    XIBOUTLET UILabel *header_;
    XIBOUTLET UITextView *message_;    
    XASSIGN id _delegate;    
    XASSIGN int counter;    
    XRETAIN NSArray *listOfUsers_;    
    XCOPY NSString *secretKey_;
    int age;
}

@property (nonatomic, assign) int counter;
@property (nonatomic, assign) id delegate;
@property (nonatomic, retain) IBOutlet UILabel *header;
@property (nonatomic, retain) NSArray *listOfUsers;
@property (nonatomic, retain) IBOutlet UITextView *message;
@property (nonatomic, copy) NSString *secretKey;

- (IBAction)doSomething:(id)sender;

@end
