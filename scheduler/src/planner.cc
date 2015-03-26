
#include "planner.h"
#include "base/time.h"
#include "base/string_util.h"
#include "order_types.h"

using namespace base;

namespace scheduler {

void Planner::Run() {
  while (true) {

    while (carpool_rmq_.Len() > 0) {
      ReplyObj robj;
      robj = carpool_rmq_.Pop();
      if (robj.OK()) {
        std::string str(robj.Str(), robj.Len());
        PoolOrder* pool_order = new PoolOrder();
        if (thrift_.StringToThrift(str, pool_order)) {
          VLOG(2) << "pool order " << pool_order->id;
          ProcessPoolOrder(pool_order);
        } else {
          //TODO:
          delete pool_order;
        }
      }
    } 

    usleep(2000000);
  }

}

void Planner::ProcessPoolOrder(PoolOrder* pool_order) {
  ReplyObj robj;
  HistoryDriver hd;
  std::string pool_id = pool_order->id;
  
  // get history driver
  robj = history_driver_rm_.Get(pool_id); 
  if (robj.OK() && robj.Len() > 0) {
    std::string hdstr(robj.Str(), robj.Len());
    if (!thrift_.StringToThrift(hdstr, &hd)) {
      LOG(ERROR) << "failed to get history driver " << pool_order->id;
    }
  }

  // driver process: 
  const Path& path = pool_order->order_list[0].path;
  std::string path_id = path.from_city + "-" + path.to_city;
 
  int history_num = hd.drivers.size();
  
  // 1. reduce history drivers priority
  if (history_num == 1) {
    VLOG(2) << "change priority for " << path_id;
    ChangePriority(path_id, hd.drivers);
  }
  
  // 2. fetch new drivers
  int fetch_num = std::max(history_num << 1, 1);
  robj = driver_rpq_.GetWithScore(path_id, 0, fetch_num);
  VLOG(2) << "fetch " << fetch_num << " drivers";
  
  pool_order->drivers.clear();
  for (size_t i = 0; i < robj.Num(); ++i) {
    std::string did(robj.Ele(i)->str);
    int new_driver_index = -1;
    
    int priority = (i & 0x01 > 0)? StringToInt(did) : -1;

    VLOG(4) << "1: did->" << did << ", priority->" << priority << ", index->" << new_driver_index;
    if (priority < 0 && hd.drivers.find(did) == hd.drivers.end()) {
      Driver one;
      one.phone = did;
      pool_order->drivers.push_back(one);
      new_driver_index = (int)(pool_order->drivers.size() - 1);
    }

    VLOG(4) << "2: did->" << did << ", priority->" << priority << ", index->" << new_driver_index;
    if (priority >= 0 && new_driver_index > 0) {
      pool_order->drivers[new_driver_index].priority = priority;
    }
  }

  // no new drivers available
  if (pool_order->drivers.size() == 0) {
    VLOG(2) << "no new drivers available for " << pool_order->id;
    pool_order->pushtime = GetTimeInMs();
    queue_->Push(pool_order);
    return;
  }
   
  // send message:
  VLOG(2) << "send message: " << pool_order->id;
  SendMessage(pool_order);

  // 3. record new history drivers
  VLOG(2) << "record new history drivers for " << pool_order->id;
  for (size_t i = 0; i < pool_order->drivers.size(); ++i) {
    hd.drivers.insert(pool_order->drivers[i].phone);
  }
  std::string hdstr = ThriftToString(&hd);
  history_driver_rm_.Set(pool_id, hdstr);

  // send to re-pack queue
  VLOG(2) << "put to repacker queue";
  pool_order->pushtime = GetTimeInMs();
  queue_->Push(pool_order);
}

void Planner::ChangePriority(const std::string& path_id, const std::set<std::string>& drivers) {
  std::set<std::string>::iterator it;
  for (it = drivers.begin(); it != drivers.end(); it++) {
    int score = driver_rpq_.Update(path_id, *it, -1);
    if (score < 0) {  // not exist
      driver_rpq_.Del(path_id, *it);
    }
  }
}

void Planner::SendMessage(const PoolOrder* pool_order) {
  Message msg;
  msg.template_type = 0;  // transmission template
  msg.push_type = 1;  // to list
  msg.app_type = 1; // to driver
  msg.title = "pool_order";
  msg.text = "";
  msg.url = "";
  
  // set message content
  msg.content = ThriftToString(pool_order);
  for (size_t i = 0; i < pool_order->drivers.size(); ++i) {
    VLOG(3) << "push " << pool_order->id << " to " << pool_order->drivers[i].phone;
    msg.target.push_back(pool_order->drivers[i].phone);
  }

  // put message to redis
  std::string msgbuf = ThriftToString(&msg);
  msg_rq_.Put(msgbuf); 

}


}  // end namespace
