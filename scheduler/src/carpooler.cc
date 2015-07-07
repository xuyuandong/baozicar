
#include <algorithm>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <boost/uuid/uuid_generators.hpp>
#include "carpooler.h"
#include "order_types.h"
#include "base/string_util.h"
#include "base/time.h"

DEFINE_int32(batch_size, 10, "threshold size for batch clustering");
DEFINE_int32(output_size, 4, "threshold size for output poolorder");
DEFINE_int32(pool_size, 3, "carpool max size");
DEFINE_int64(cluster_interval, 300, "carpool cluster time interval");
DEFINE_int64(subsidy_duration, 1800, "subsidy time duration");
DEFINE_int32(sleep_msec_carpooler, 5000, "sleep time in milli-seconds when scheduler is waiting");
DEFINE_int32(subsidy_cache_expire_time, 3600, "expire time in seconds for subsidy cache re-read redis");

using namespace boost::unordered;

namespace scheduler {

void Carpooler::Run() {
  while (true) {
    
    std::vector<PoolOrder*> pool_vec;
    
    while (!in_queue_->Empty()) {
      Order* order = NULL;
      in_queue_->Pop(order);
      VLOG(4) << "transport an order " << order->id;

      // assign the order to its path
      std::string path_id = order->path.from_city + "-" + order->path.to_city;
      if (batch_map_.find(path_id) == batch_map_.end()) {
        batch_map_[path_id] = new std::vector<Order*>();
        path_count_map_[path_id] = 0;
      }
      batch_map_[path_id]->push_back(order);
      path_count_map_[path_id] += order->number;

      // batch clustering if some path's orders could 
      bool timeout = CheckTimeOut(path_id);
      timeout = timeout || (path_count_map_[path_id] > FLAGS_batch_size);
      VLOG(4) << "timeout flag = " << timeout;
      if (timeout) {
        VLOG(2) << "batch clustering " << path_id;
        Clustering(path_id, pool_vec, timeout);  // NOTE: will change batch_map_ and path_count_map_  
      } else {
        VLOG(2) << "process left orders " << path_id;
        ProcessLeftOrders(path_id);
      }

      // output several times to protect poolorder vector to be too large at busy times
      if (pool_vec.size() > 0) {
        VLOG(2) << "output carpool ...";
        OutputCarpool(pool_vec);
      }
    }
    
    // sleep
    if (in_queue_->Empty()) {
      VLOG(5) << "carpooler sleep " << FLAGS_sleep_msec_carpooler << " msec";
      base::MilliSleep(FLAGS_sleep_msec_carpooler);
    }
  }
}

bool Carpooler::CheckTimeOut(const std::string& path_id) {
  bool timeout = false;
  int64_t current_time = base::GetTimeInSec() ;

  if (path_time_map_.find(path_id) == path_time_map_.end()) {
    // first clustering time
    path_time_map_[path_id] = current_time;
    timeout = true;
  } else {
    // check last clustering timestamp
    int64_t last_time = path_time_map_[path_id];
    int64_t interval = (current_time - last_time);
    if (interval > FLAGS_cluster_interval) {
      path_time_map_[path_id] = current_time;
      timeout = true;
    }
  }
  return timeout;
}

void Carpooler::AddSpecialOrder(Order* order, std::vector<PoolOrder*>& pool_vec) {
  std::vector<std::string> stations;
  station_manager_.FetchStations(order, &stations);

  PoolOrder* po = new PoolOrder();
  po->order_list.push_back(*order);
  po->cartype = SPECIAL;
  po->__set_from_station(stations.front());
  po->__set_to_station(stations.back());

  pool_vec.push_back(po);
}


void Carpooler::Clustering(const std::string& path_id, std::vector<PoolOrder*>& pool_vec, bool timeout) {
  std::vector<Order*>& order_vec = *batch_map_[path_id]; // all possible orders
  std::vector<Order*> orders;  // keep temporal carpooling orders
  
  VLOG(3) << "special car clustering ...";
  for (size_t i = 0; i < order_vec.size(); ++i) {
    if (order_vec[i]->cartype == SPECIAL) {
      AddSpecialOrder(order_vec[i], pool_vec);
      delete order_vec[i]; 
      order_vec[i] = NULL;
    } else {  // carpool order
      orders.push_back(order_vec[i]);
    }
  }
  
  // check if not timeout, no need to clustering
  if (!timeout) { 
    VLOG(3) << "not time out, go back ...";
    // no need to do clustering this time
    order_vec.swap(orders);
    // re-count path size
    int path_size = 0;
    for (size_t i = 0; i < order_vec.size(); ++i) {
      path_size += order_vec[i]->number;
    }
    path_count_map_[path_id] = path_size;
    return;
  } 

  VLOG(3) << "partition " << path_id << " into stations ..."; 
  unordered_map<std::string, std::vector<Order*> > station_map;        
  std::vector<std::string> stations;
  for (size_t i = 0; i < orders.size(); ++i) {
    station_manager_.FetchStations(orders[i], &stations);
    std::string tag = stations.front() + "|" + stations.back();
    
    if (station_map.find(tag) == station_map.end()) {
      station_map[tag] = std::vector<Order*>();
    }
    station_map[tag].push_back(orders[i]);
  }

  //
  unordered_map<std::string, std::vector<Order*> >::iterator it;
  
  VLOG(3) << "carpool clustering within each station tag ...";
  for (it = station_map.begin(); it != station_map.end(); ++it) {
    BatchClustering(it->first, it->second, pool_vec);
  }

  VLOG(3) << "check subsidy for long waiting order";
  int ssprice = GetSubsidyPrice(path_id);
  VLOG(4) << "get subsidy " << ssprice << " for " << path_id;
  for (it = station_map.begin(); it != station_map.end(); ++it) {
    if (it->second.size() > 0) {
      if (ssprice > 0) {
        const std::string& tag = it->first;
        CheckOrSubsidyOrder(tag, ssprice, it->second, pool_vec);
      } else {
        const std::vector<Order*>& vec = it->second;
        for (size_t i = 0; i < vec.size(); ++i) {
          out_queue_->Push(vec[i]);
        }
      }
      // reset memory
      it->second.clear();
    }
  }  // end for

  VLOG(4) << "reset memory for path " << path_id;
  batch_map_[path_id]->clear(); // all possible orders
  path_count_map_[path_id] = 0;
}

void Carpooler::ProcessLeftOrders(const std::string& path_id) {
  std::vector<Order*>& left_orders = *batch_map_[path_id];
  for (size_t i = 0; i < left_orders.size(); ++i) {
    out_queue_->Push(left_orders[i]);
  }
  batch_map_[path_id]->clear();
  path_count_map_[path_id] = 0;
}


bool CompareOrder(const Order* o1, const Order* o2) {
  return o1->number > o2->number;
}

void Carpooler::BatchClustering(const std::string& tag, 
    std::vector<Order*>& orders, std::vector<PoolOrder*>& pool_vec) {
  std::vector<std::string> stations;
  SplitString(tag, '|', &stations);
  
  std::sort(orders.begin(), orders.end(), CompareOrder);

  int head = 0, tail = orders.size();
  for (;head < tail;) {
    PoolOrder* po = new PoolOrder();
    int count = 0;
    int beg = head;
    int end = tail - 1;

    VLOG(4) << "->" << head << " " << tail << " " << beg << " " << end;
    while (beg < tail) {
      if (count + orders[beg]->number > FLAGS_pool_size)
        break;
      count += orders[beg]->number;
      po->order_list.push_back(*orders[beg]);
      beg ++;
    }
    
    VLOG(4) << "->" << head << " " << tail << " " << beg << " " << end;
    while (beg < end) {
      if (count + orders[end]->number > FLAGS_pool_size)
        break;
      count += orders[end]->number;
      po->order_list.push_back(*orders[end]);
      end --;
    }
    
    VLOG(4) << "->" << head << " " << tail << " " << beg << " " << end;
    if (count == FLAGS_pool_size) {
      VLOG(4) << "find one carpool !!!";
      po->cartype = CARPOOL;
      po->__set_from_station(stations.front());
      po->__set_to_station(stations.back());
      pool_vec.push_back(po);

      head = beg;
      tail = end + 1;
    } else {
      delete po;
      po = NULL;
      break;
    }
    VLOG(4) << "->" << head << " " << tail << " " << beg << " " << end;
  }

  // put left orders into original vector, delete carpooling orders ...
  VLOG(3) << "keep left orders, delete carpooled orders ...";
  std::vector<Order*> tmp_vec;
  for (size_t i = 0; i < orders.size(); ++i) {
    if (i < head || i >= tail) {
      delete orders[i];
      orders[i] = NULL;
    } else {
      tmp_vec.push_back(orders[i]);
    }
  }
  orders.clear();
  orders.swap(tmp_vec);

}


int Carpooler::GetSubsidyPrice(const std::string& path_id) {
  int64_t current_time = base::GetTimeInSec() ;
  if (current_time < cache_timestamp_) {
    if (cache_.find(path_id) != cache_.end()) {
      return cache_[path_id];
    }
  } else {  // cache expire
    cache_.clear();
  }  
 
  // fetch redis
  int subsidy_price = -1;
  base::ReplyObj robj;
  robj = path_rsm_.Get(path_id, "pc_price");
  if (robj.OK()) {
    std::string price_str(robj.Str());
    subsidy_price = StringToInt(price_str);
  }

  // write to cache
  if (cache_.size() == 0) {
    cache_timestamp_ = current_time + FLAGS_subsidy_cache_expire_time; 
  }
  cache_[path_id] = subsidy_price;
  return subsidy_price;
}

void Carpooler::CheckOrSubsidyOrder(const std::string& tag, int subsidy_price, 
    std::vector<Order*>& orders, std::vector<PoolOrder*>& pool_vec) {
  int64_t current_time = base::GetTimeInSec();
  std::vector<PoolOrder*> ss_po_vec;
  std::vector<Order*> left_orders;
  
  // seperate timeout and un-timeout order
  VLOG(3) <<  "seperate timeout and un-timeout order ";
  for (size_t i = 0; i < orders.size(); ++i) {
    int64_t duration = (current_time - orders[i]->time);
    
    if (duration > FLAGS_subsidy_duration) {
      VLOG(4) << "there is a timeout order " << orders[i]->id;
      // cluster timeout orders
      bool match = false;
      for (size_t j = 0; j < ss_po_vec.size(); ++j) {
        PoolOrder* po = ss_po_vec[j];
        if (po->number + orders[i]->number <= FLAGS_pool_size) {
          po->number += orders[i]->number;
          po->order_list.push_back(*orders[i]);
          match = true;
          break;
        }
      }

      if (!match) {
        PoolOrder* po = new PoolOrder();
        po->cartype = CARPOOL;
        po->sstype = SUBSIDY;
        po->number = orders[i]->number;
        po->order_list.push_back(*orders[i]);
        ss_po_vec.push_back(po);
      }
     
      // timeout orders must be deleted
      delete orders[i];
      orders[i] = NULL;
     
    } else {
      // keep not timeout orders into 'left_orders'
      left_orders.push_back(orders[i]);
    }
  }
  orders.clear();

  // check left not timeout orders if could be clustered
  VLOG(3) << "check left not timeout orders if could be clustered";
  for (size_t i = 0; i < left_orders.size(); ++i) {
    bool match = false;
    
    for (size_t j = 0; j < ss_po_vec.size(); ++j) {
      PoolOrder* po = ss_po_vec[j];
      if (po->number + left_orders[i]->number <= FLAGS_pool_size) {
        po->order_list.push_back(*left_orders[i]);
        po->number += left_orders[i]->number;
        match = true;
        break;
      }
    }

    if (!match) {
      out_queue_->Push(left_orders[i]);
    } else {
      delete left_orders[i];
      left_orders[i] = NULL;
    }
  } 

  // write subsidy price
  VLOG(3) <<  "write subsidy price / stations ... ";
  std::vector<std::string> stations;
  SplitString(tag, '|', &stations);
  
  for (size_t i = 0; i < ss_po_vec.size(); ++i) {
    int need = FLAGS_pool_size - ss_po_vec[i]->number;
    ss_po_vec[i]->subsidy = need * subsidy_price;
    ss_po_vec[i]->__set_from_station(stations.front());
    ss_po_vec[i]->__set_to_station(stations.back());
    pool_vec.push_back(ss_po_vec[i]); 
  }
}


void Carpooler::SetPoolId(PoolOrder* pool_order) {
  boost::uuids::uuid id = boost::uuids::random_generator()();
  pool_order->id = boost::uuids::to_string(id);
}

void Carpooler::OutputCarpool(std::vector<PoolOrder*>& pool_vec) {
  for (size_t i = 0; i < pool_vec.size(); ++i) {
    SetPoolId(pool_vec[i]);
    std::string val;
    if (thrift_.ThriftToString(pool_vec[i], &val)) {
      const std::string& key = pool_vec[i]->id;
      VLOG(2) << "out poolorder " << key;
      rmq_.Put(key, val);
    } else {
      //TODO: how to deal with failed pool order
      VLOG(2) << "failed to make thrift string, re-send to revoker";
    }
    
    delete pool_vec[i]; 
    pool_vec[i] = NULL;
  }
  pool_vec.clear();
}

}  // end namespace
