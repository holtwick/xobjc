#import "DemoViewController.h"

@implementation DemoViewController

@synthesize counter;
@synthesize delegate = _delegate;
@synthesize header = header_;
@synthesize listOfUsers = listOfUsers_;
@synthesize message = message_;
@synthesize secretKey = secretKey_;

XPUBLIC
- (IBAction)doSomething:(id)sender {
    NSLog(@"Doing something");
}

- (void)viewDidUnload{
    [super viewDidUnload];

    self.delegate = nil;

    self.header = XNIL;
    self.message = XNIL;
}

- (void)dealloc{
    [header_ release];
    [listOfUsers_ release];
    [message_ release];
    [secretKey_ release];
    [super dealloc];
}

@end
