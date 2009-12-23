/*
 
 Apply `xobjc` to this file to see the effect 
 
 */

#import "DemoViewController.h"

@implementation DemoViewController

// X PUBLIC
- (IBAction)doSomething:(id)sender {
    NSLog(@"Doing something");
}

- (void)viewDidUnload{
    [super viewDidUnload];
    self.delegate = nil;
}

@end
