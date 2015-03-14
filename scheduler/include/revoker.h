#ifndef _REVOKER_H_
#define _REVOKER_H_

#include "base/concurrent_queue.h"
#include "connector.h"

namespace scheduler {

class Order;

class Revoker : public Connector {
  public:
    Revoker(const std::string& host, int port) 
      :Connector(host.c_str(), port) {}
    virtual ~Revoker() {}

    void SetupOutputRedis(const std::string& order_rmq_name) {
      rmq_.Init(&this->redis_, order_rmq_name);
    }

    void SetupInputQueue(base::ConcurrentQueue<Order*>* q) {
      queue_ = q;
    }

  protected:
    virtual void Run();

  private:
    base::ConcurrentQueue<Order*>* queue_;
    base::RedisMapQueue rmq_;
};

}  // namespace scheduler

#endif  // _REVOKER_H_
