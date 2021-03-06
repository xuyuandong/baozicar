#ifndef _CARPOOLER_H_
#define _CARPOOLER_H_

#include <map>
#include <vector>
#include <boost/unordered_map.hpp>
#include "base/concurrent_queue.h"
#include "connector.h"
#include "stations.h"
#include "cache.h"

namespace scheduler {

class Order;
class PoolOrder;

class Carpooler : public Connector {
  public:
    Carpooler(const std::string& host, int port);
    virtual ~Carpooler() {}

    void SetupOutputRedis(const std::string& carpool_rmq_name) {
      rmq_.Init(&this->redis_, carpool_rmq_name);
    }

    void SetupPathRedis(const std::string& path_rsm_name) {
      path_rsm_.Init(&this->redis_, path_rsm_name);
    }

    void SetupQueue(base::ConcurrentQueue<Order*>* inq,
        base::ConcurrentQueue<Order*>* outq) {
      in_queue_ = inq;
      out_queue_ = outq;
    }

  protected:
    void Clustering(const std::string& path_id, std::vector<PoolOrder*>& pool_vec, bool timeout);

    bool CheckLoopTimeout();

    bool CheckTimeOut(const std::string& path_id);
    
    void AddSpecialOrder(Order* order, std::vector<PoolOrder*>& pool_vec);
    
    int GetPoolSize(const std::string& path_id);
    int GetSubsidyPrice(const std::string& path_id);

    void BatchClustering(const std::string& path_id, const std::string& tag, 
        std::vector<Order*>& orders, std::vector<PoolOrder*>& pool_vec);

    void CheckOrSubsidyOrder(const std::string& tag, int subsidy_price, 
        std::vector<Order*>& order_vec, std::vector<PoolOrder*>& pool_vec);

    void SetPoolId(PoolOrder* pool_order);
    
    void OutputCarpool(std::vector<PoolOrder*>& pool_vec);

  protected:
    virtual void Run();

  private:
    base::RedisMapQueue rmq_;
    base::RedisStructMap path_rsm_;

    base::ConcurrentQueue<Order*>* in_queue_;
    base::ConcurrentQueue<Order*>* out_queue_;

    boost::unordered::unordered_map<std::string, int> path_count_map_;
    boost::unordered::unordered_map<std::string, int64_t> path_time_map_;
    boost::unordered::unordered_map<std::string, std::vector<Order*>* > batch_map_;        

    // for loop path clustering
    int64_t loop_timestamp_;

    // for pool_size/subsidy cache
    Cache<int> subsidy_cache_;
    Cache<int> pool_size_cache_;

    // for path station 
    StationManager station_manager_;
};

}  // namespace scheduler

#endif  // _CARPOOLER_H_
