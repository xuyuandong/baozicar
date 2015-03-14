#ifndef _DISPATCHER_H_
#define _DISPATCHER_H_

#include "base/concurrent_queue.h"
#include "connector.h"

namespace scheduler {

class Order;

class Dispatcher: public Connector {
  public:
    Dispatcher(const std::string& host, int port) 
      :Connector(host.c_str(), port) {}
    virtual ~Dispatcher() {}

    void SetupInputRedis(const std::string& order_rmq_name) {
      rmq_.Init(&this->redis_, order_rmq_name);
    }

    void SetupOutputQueue(base::ConcurrentQueue<Order*>* q) {
      queue_ = q;
    }

  protected:
    virtual void Run();

  private:
    base::ConcurrentQueue<Order*>* queue_;
    base::RedisMapQueue rmq_;
};

}  // namespace scheduler

#endif  // _DISPATCHER_H_
