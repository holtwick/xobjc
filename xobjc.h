//
//  xobjc.h
//
//  Created by Dirk Holtwick 
//  Copyright holtwick.it 2009. All rights reserved.
//
 

#define XRETAIN 
#define XIBOUTLET
#define XASSIGN
#define XCOPY 
#define XPROPERTY(...)

#define XNIL nil

#define XPUBLIC 

#define XINSTANCE(klass) \
+ (id)instance { \
  static klass *instance = nil; \
  @synchronized (self) { \
    if (!instance) { \
        instance = [[[klass alloc] init] autorelease]; \
    } \
  } \
  return instance; \
}
