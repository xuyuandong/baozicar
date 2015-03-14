
#include <algorithm>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <boost/uuid/uuid_generators.hpp>
#include "carpooler.h"
#include "order_types.h"
#include "base/string_util.h"

DEFINE_int32(batch_size, 10, "threshold size for batch clustering");
DEFINE_int32(output_size, 4, "threshold size for output poolorder");
DEFINE_int32(pool_size, 3, "carpool max size");

using namespace boost::unordered;

namespace scheduler {

void Carpooler::Run() {
  while (true) {
    
    int max_path_size = 0;
    std::vector<PoolOrder*> pool_vec;
    
    while (!in_queue_->Empty()) {
      Order* order = NULL;
      in_queue_->Pop(order);

      // assign the order to its path
      std::string path_id = order->path.from_city + "-" + order->path.to_city;
      if (batch_map_.find(path_id) == batch_map_.end()) {
        batch_map_[path_id] = new std::vector<Order*>();
        path_count_map_[path_id] = 0;
      }
      batch_map_[path_id]->push_back(order);
      path_count_map_[path_id] += order->number;

      // batch clustering if some path's orders could 
      if (path_count_map_[path_id] > FLAGS_batch_size) {
        VLOG(2) << "1. batch clustering " << path_id;
        BatchClustering(path_id, pool_vec);  // NOTE: will change batch_map_ and path_count_map_  
      }

      // mark left orders size of the path
      if (path_count_map_[path_id] > max_path_size)
        max_path_size = path_count_map_[path_id];
    
      // output several times to protect poolorder vector to be too large at busy times
      if (pool_vec.size() > FLAGS_output_size) {
        OutputCarpool(pool_vec);
        for (size_t i = 0; i < pool_vec.size(); ++i) {
          delete pool_vec[i]; 
          pool_vec[i] = NULL;
        }
        pool_vec.clear();
      }
    }
    
    // batch clustering if it could
    if (max_path_size >= FLAGS_pool_size) {
      unordered_map<std::string, std::vector<Order*>* >::iterator it;
      for (it = batch_map_.begin(); it != batch_map_.end(); ++it) {
        VLOG(2) << "2. batch clustering " << it->first;
        BatchClustering(it->first, pool_vec);  // NOTE: will change batch_map_ and path_count_map_  
      }
    }

    // process left orders, and clear batch_map_
    ProcessLeftOrders(pool_vec);  // NOTE: will change batch_map_ and path_count_map_  

    // send carpooling result to redis queue
    if (pool_vec.size() > 0) {
      OutputCarpool(pool_vec);
      for (size_t i = 0; i < pool_vec.size(); ++i) {
        delete pool_vec[i]; 
        pool_vec[i] = NULL;
      }
      pool_vec.clear();
    }

    // sleep
    if (in_queue_->Empty()) {
      usleep(100000);
    }
  }
}

bool CompareOrder(const Order* o1, const Order* o2) {
  return o1->number > o2->number;
}

void Carpooler::BatchClustering(const std::string& path_id, std::vector<PoolOrder*>& pool_vec) {

  std::vector<Order*>& order_vec = *batch_map_[path_id]; // all possible orders
  std::vector<Order*> orders;  // carpooling orders

  // deal with special car
  for (size_t i = 0; i < order_vec.size(); ++i) {
    if (order_vec[i]->cartype == SPECIAL) {
      AddSpecialOrder(order_vec[i], pool_vec);

    } else {  // carpool
      orders.push_back(order_vec[i]);
    }
  }
  
  // deal with pooling car
  std::sort(orders.begin(), orders.end(), CompareOrder);

  int head = 0, tail = orders.size();
  for (;head < tail;) {
    PoolOrder* po = new PoolOrder();
    int count = 0;
    int beg = head;
    int end = tail - 1;

    while (beg < tail) {
      if (count + orders[beg]->number > FLAGS_pool_size)
        break;
      count += orders[beg]->number;
      po->order_list.push_back(*orders[beg]);
      beg ++;
    }
    
    while (beg < end) {
      if (count + orders[end]->number > FLAGS_pool_size)
        break;
      count += orders[end]->number;
      po->order_list.push_back(*orders[end]);
      end --;
    }
    
    if (count == FLAGS_pool_size) {
      po->cartype = CARPOOL;
      pool_vec.push_back(po);

      head = beg;
      tail = end + 1;
    } else {
      delete po;
      po = NULL;
      break;
    }
  }

  // keep left orders, delte carpooling orders ...
  std::vector<Order*> left_order_vec;
  for (;head < tail;) {
    left_order_vec.push_back(orders[head++]);
  }

  for (int i = 0; i < head; ++i) {
    delete orders[i];
    orders[i] = NULL;
  }
  for (size_t i = tail; i < orders.size(); ++i) {
    delete orders[i];
    orders[i] = NULL;
  }
  
  // put left orders into original vector
  order_vec.swap(left_order_vec);
  
  // re-count path size
  int path_size = 0;
  for (size_t i = 0; i < order_vec.size(); ++i) {
    path_size += order_vec[i]->number;
  }
  path_count_map_[path_id] = path_size;
}

void Carpooler::AddSpecialOrder(Order* order, std::vector<PoolOrder*>& pool_vec) {
  PoolOrder* po = new PoolOrder();
  po->order_list.push_back(*order);
  po->cartype = SPECIAL;
  
  pool_vec.push_back(po);
  
  delete order; 
  order = NULL;
}

void Carpooler::ProcessLeftOrders(std::vector<PoolOrder*>& pool_vec) {
  unordered_map<std::string, std::vector<Order*>* >::iterator it;
  for (it = batch_map_.begin(); it != batch_map_.end(); ++it) {
    std::vector<Order*>& vec = *(it->second);
    
    for (size_t i = 0; i < vec.size(); ++i) {
      if (vec[i]->cartype == SPECIAL) {
        AddSpecialOrder(vec[i], pool_vec);
        vec[i] = NULL;
      } else {
        out_queue_->Push(vec[i]);
      }
    }

    // reset memory
    it->second->clear();
    path_count_map_[it->first] = 0;
  }
}

void Carpooler::SetPoolId(PoolOrder* pool_order) {
  boost::uuids::uuid id = boost::uuids::random_generator()();
  pool_order->id = boost::uuids::to_string(id);
}

void Carpooler::OutputCarpool(const std::vector<PoolOrder*>& pool_vec) {
  for (size_t i = 0; i < pool_vec.size(); ++i) {
    SetPoolId(pool_vec[i]);
    std::string val;
    if (thrift_.ThriftToString(pool_vec[i], &val)) {
      const std::string& key = pool_vec[i]->id;
      VLOG(2) << "out poolorder " << key;
      rmq_.Put(key, val);
    } else {
      //TODO: how to deal with failed pool order
    }
  }

}

}  // end namespace
