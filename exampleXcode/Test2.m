//
//  Copyright 2010 holtwick.it. All rights reserved.
//

#import "Test2.h"

@implementation Test2

// MARK: Methods

// ...

// MARK: Constructors

/*
+ (id)instance {
    static id instance = nil;
    @synchronized (self) {
        if (!instance) {
            instance = [[self alloc] init];
        }
    }
    return instance;
}

- (id)initWithString:(NSString *)string {
    self = [self init];
    if (self != nil) {
        self.string = string;
    }
    return self;
}

- (id)init {
    self = [super init];
    if (self != nil) {
        ;
    }
    return self;
}
*/

- (void)dealloc {
    [x xrelease];
    [super dealloc];
}

@synthesize x;

@end