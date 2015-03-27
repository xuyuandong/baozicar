
#include "planner.h"
#include "base/time.h"
#include "base/string_util.h"
#include "order_types.h"

DEFINE_int32(sleep_msec_planner, 5000, "sleep time in milli-seconds when scheduler is waiting");
DEFINE_int32(schedule_restart_period, 3600000, "milli-second period for scheduler re-send a pool order");

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

    base::MilliSleep(FLAGS_sleep_msec_planner);
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
  
  int new_driver_index = -1;
  pool_order->drivers.clear();
  for (size_t i = 0; i < robj.Num(); ++i) {
    std::string did(robj.Ele(i)->str);
    int priority = (i & 0x01 > 0)? StringToInt(did) : -1;
    VLOG(4) << "i=" << i << " did=" << did << " priority=" << priority;
    
    if (priority < 0 && hd.drivers.find(did) == hd.drivers.end()) {
      VLOG(4) << "driver phone, assert -1=" << new_driver_index;
      Driver one;
      one.phone = did;
      pool_order->drivers.push_back(one);
      new_driver_index = (int)(pool_order->drivers.size() - 1);
    }

    if (priority >= 0 && new_driver_index > 0) {
      VLOG(4) << "driver priority, index=" << new_driver_index;
      pool_order->drivers[new_driver_index].priority = priority;
      new_driver_index = -1;
    }
  }


  if (pool_order->drivers.size() > 0) {
    // send message, update pushtime:
    VLOG(2) << "send message: " << pool_order->id;
    pool_order->pushtime = GetTimeInMs();
    SendMessage(pool_order);

    // record new history drivers
    VLOG(2) << "record new history drivers for " << pool_order->id;
    for (size_t i = 0; i < pool_order->drivers.size(); ++i) {
      hd.drivers.insert(pool_order->drivers[i].phone);
    }
    std::string hdstr = ThriftToString(&hd);
    history_driver_rm_.Set(pool_id, hdstr);

  } else {
    // no new drivers available
    VLOG(2) << "no new drivers available for " << pool_order->id;
  
    // check if timeout, clear history driver and re-send
    int64_t duration = base::GetTimeInMs() - pool_order->pushtime;
    if (duration > FLAGS_schedule_restart_period) {
      VLOG(2) << "clear history driver and re-start sending loop";
      history_driver_rm_.Del(pool_id);
    }

  }
   
  // send to re-pack queue
  VLOG(2) << "put to repacker queue";
  queue_->Push(pool_order);
}

void Planner::ChangePriority(const std::string& path_id, const std::set<std::string>& drivers) {
  std::set<std::string>::iterator it;
  for (it = drivers.begin(); it != drivers.end(); it++) {
    int score = driver_rpq_.Update(path_id, *it, 1);
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
