#ifndef _CACHE_H_
#define _CACHE_H_

#include <map>
#include <string>
#include "base/time.h"

namespace scheduler {

template <class T>
class Cache {
  public:
    Cache(){
      timestamp_ = 0;
    }
    ~Cache(){}

    void SetExpireTime(int64_t t) {
      expire_time_ = t;
    }
    bool Fetch(const std::string& key, T* object);
    void Write(const std::string& key, const T& value);

  private:
    int64_t timestamp_;
    int64_t expire_time_;
    std::map<std::string, T> cache_;

};


template <class T>
bool Cache<T>::Fetch(const std::string& key, T* object) {
  int64_t current_time = base::GetTimeInSec() ;
  if (current_time < timestamp_) {
    VLOG(5) << "fetch cache key: " << key;
    if (cache_.empty() || cache_.find(key) != cache_.end()) {
      *object = cache_[key];
      return true;
    }
  } else {  // cache expire
    VLOG(5) << "expired, clear cache";
    cache_.clear();
  }
  return false;
}

template <class T>
void Cache<T>::Write(const std::string& key, const T& value) {
  VLOG(5) << "write to cache key: " << key;
  if (cache_.empty()) {
    int64_t current_time = base::GetTimeInSec() ;
    timestamp_ = current_time + expire_time_; 
  }
  cache_[key] = value;

}


}  // end namespace 

#endif  // _CACHE_H_
