//
//  xobjc.h
//
//  Created by Dirk Holtwick 
//  Copyright holtwick.it 2009. All rights reserved.
//
 
#define XASSIGN
#define XRETAIN 
#define XCOPY 
#define XATOMIC 
#define XREADONLY
#define XIBOUTLET

#define XNIL nil

#define XPRIVATE
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
