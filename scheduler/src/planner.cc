
#include "planner.h"
#include "base/time.h"
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

    usleep(10000);
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
    ChangePriority(path_id, hd.drivers);
  }
  
  // 2. fetch new drivers
  int fetch_num = std::max(history_num << 1, 1);
  robj = driver_rpq_.Get(path_id, 0, fetch_num);
  
  for (size_t i = 0; i < robj.Num(); ++i) {
    std::string did(robj.Ele(i)->str);
    if (hd.drivers.find(did) == hd.drivers.end()) {
      pool_order->drivers.push_back(did);
    }  
  }

  // no new drivers available
  if (pool_order->drivers.size() == 0) {
    pool_order->pushtime = GetTimeInMs();
    queue_->Push(pool_order);
    return;
  }
   
  // send message:
  SendMessage(pool_order);

  // 3. record new history drivers
  for (size_t i = 0; i < pool_order->drivers.size(); ++i) {
    hd.drivers.insert(pool_order->drivers[i]);
  }
  std::string hdstr = ThriftToString(&hd);
  history_driver_rm_.Set(pool_id, hdstr);

  // send to re-pack queue
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

  // put message to redis
  std::string msgbuf = ThriftToString(&msg);
  msg_rq_.Put(msgbuf); 

}


}  // end namespace
