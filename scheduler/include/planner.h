#ifndef _PLANNER_H_
#define _PLANNER_H_

#include <set>
#include "connector.h"

namespace scheduler {

class Order;
class PoolOrder;

class Planner : public Connector {
  public:
    Planner(const std::string& host, int port) 
      :Connector(host.c_str(), port) {}
    virtual ~Planner() {}

    void SetupInputRedis(const std::string& carpool_rmq_name) {
      carpool_rmq_.Init(&this->redis_, carpool_rmq_name);
    }

    void SetupOutputRedis(const std::string& msg_rq_name) {
      msg_rq_.Init(&this->redis_, msg_rq_name);
    }

    void SetupAssitRedis(const std::string& driver_rpq_name,
        const std::string& hd_rm_name ) {
      driver_rpq_.Init(&this->redis_, driver_rpq_name);
      history_driver_rm_.Init(&this->redis_, hd_rm_name);
    }

    void SetupOutputQueue(base::ConcurrentQueue<PoolOrder*>* q) {
      queue_ = q;
    }

  protected:
    virtual void Run();

    void ProcessPoolOrder(PoolOrder* pool_order);

    void ChangePriority(const std::string& path_id, const std::set<std::string>& drivers);
    void SendMessage(const PoolOrder* pool_order);

  private:
    base::RedisQueue msg_rq_;
    base::RedisMap history_driver_rm_;
    base::RedisPriorityQueue driver_rpq_;
    base::RedisMapQueue carpool_rmq_;  // input carpool map queue
    base::ConcurrentQueue<PoolOrder*>* queue_;  // output scheduling queue

};

}  // namespace scheduler

#endif  // _PLANNER_H_
