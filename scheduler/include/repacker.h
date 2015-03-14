#ifndef _REPACKER_H_
#define _REPACKER_H_

#include "connector.h"

namespace scheduler {

class PoolOrder;

class Repacker : public Connector {
  public:
    Repacker(const std::string& host, int port) 
      :Connector(host.c_str(), port) {}
    virtual ~Repacker() {}
 
    void SetupOutputRedis(const std::string& carpool_rmq_name) {
      carpool_rmq_.Init(&this->redis_, carpool_rmq_name);
    }

    void SetupCheckRedis(const std::string& order_rmq_name) {
      order_rmq_.Init(&this->redis_, order_rmq_name);
    }

    void SetupInputQueue(base::ConcurrentQueue<PoolOrder*>* q) {
      queue_ = q;
    }

  protected:
    virtual void Run();

    void CheckAndWait(PoolOrder* pool_order);

  private:
    base::RedisMapQueue carpool_rmq_;  // carpool map queue for planner
    base::RedisMapQueue order_rmq_;    // order map queue for checking output

    base::ConcurrentQueue<PoolOrder*>* queue_;
};

}  // namespace scheduler

#endif  // _REPACKER_H_
