#ifndef _COMMON_H_
#define _COMMON_H_

#include <errno.h>

//
// This provides a wrapper around system calls which may be interrupted by a
// signal and return EINTR. See man 7 signal.
//
#define HANDLE_EINTR(x) ({ \
  int __eintr_result__; \
  do { \
    __eintr_result__ = x; \
  } while (__eintr_result__ == -1 && errno == EINTR); \
  __eintr_result__;\
})

// A macro to disallow the copy constructor and operator= functions
// This should be used in the private: declarations for a class
#define DISALLOW_COPY_AND_ASSIGN(TypeName) \
  private:                                 \
  TypeName(const TypeName&);               \
  void operator=(const TypeName&)

// Annotate a function indicating the caller must examine the return value.
// Use like:
//   int foo() WARN_UNUSED_RESULT;
// To explicitly ignore a result, see |ignore_result()| in <base/basic_types.h>.
#if defined(COMPILER_GCC)
#define WARN_UNUSED_RESULT __attribute__((warn_unused_result))
#else
#define WARN_UNUSED_RESULT
#endif

//typedef uint8_t uint8;
//typedef int32_t int32;
//typedef int64_t int64;


#endif // _COMMON_H_


