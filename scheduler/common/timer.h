#ifndef _TIMER_H_
#define _TIMER_H_

#include <chrono>

namespace base {

class Timer {
 public:
  typedef std::chrono::high_resolution_clock HighResolutionClock;
  typedef std::chrono::milliseconds MilliSeconds;
  typedef std::chrono::nanoseconds  NanoSeconds;

  Timer() : start_time_point_(HighResolutionClock::now()) {}
  
  uint64_t ElapsedMilliSeconds() const {
    return std::chrono::duration_cast<MilliSeconds>(
               HighResolutionClock::now() - start_time_point_)
              .count();
  }
  uint64_t ElapsedNanoSeconds() const {
    return std::chrono::duration_cast<NanoSeconds>(
               HighResolutionClock::now() - start_time_point_)
               .count();
  }

  void Reset() {
    start_time_point_ = HighResolutionClock::now();
  }

 protected:
  HighResolutionClock::time_point start_time_point_;
};

}  // end namespace

#endif  // _TIMER_H_
