#ifndef _CONNECTOR_H_
#define _CONNECTOR_H_

#include <base/thread.h>
#include <base/concurrent_queue.h>
#include "redispp.h"
#include "thrift.h"

namespace scheduler {

enum CarType {
  CARPOOL = 0,
  SPECIAL = 1,
  BOOKING = 2
};

enum PoolType {
  NORMAL = 0,
  SUBSIDY = 1
};

class Connector : public base::Thread {
  public:
    Connector(const char* host, int port)
      : redis_(host, port) {
      SetJoinable(true);
      stop_ = false;
    }
    virtual ~Connector() {}

    void Stop() { 
      stop_ = true;
    }

  protected:
    virtual void Run() = 0;

    bool stop_;
    base::Redispp redis_;
    base::ThriftTool thrift_;

  DISALLOW_COPY_AND_ASSIGN(Connector);

};

}  // namespace scheduler

#endif  // _CONNECTOR_H_
