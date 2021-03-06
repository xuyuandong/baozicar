
#include "planner.h"
#include "base/time.h"
#include "base/string_util.h"
#include "order_types.h"

DEFINE_int32(sleep_msec_planner, 5000, "sleep time in milli-seconds when scheduler is waiting");
DEFINE_int32(schedule_restart_period, 3600, "second period for scheduler re-send a pool order");
DEFINE_int32(fixed_push_num, 20, "fixed driver num for one push");

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

    VLOG(5) << "planner sleep " << FLAGS_sleep_msec_planner << " msec";
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
  //int history_num = hd.drivers.size();
  const Path& path = pool_order->order_list[0].path;
  std::string path_id = path.from_city + "-" + path.to_city;
  
  // 1. reduce history drivers priority
  /*if (history_num == 1 && !hd.reduced) {
    VLOG(2) << "change priority for " << path_id;
    ChangePriority(path_id, hd.drivers);
    hd.reduced = true;
  }*/
  
  // 2. fetch new drivers
  //int fetch_num = std::max(history_num << 1, 1);
  int fetch_num = FLAGS_fixed_push_num;
  robj = driver_rpq_.GetWithScore(path_id, 0, fetch_num);
  VLOG(2) << "fetch " << fetch_num << " drivers";
  
  int new_driver_index = -1;
  pool_order->drivers.clear();
  for (size_t i = 0; i < robj.Num(); ++i) {
    std::string did(robj.Ele(i)->str);
    bool isphone = (i % 2 == 0);
    VLOG(4) << "isphone=" << isphone << " did=" << did;
    
    if (isphone) {
      if (hd.drivers.find(did) == hd.drivers.end()) {
        VLOG(4) << "new driver phone " << did;
        Driver one;
        one.phone = did;
        pool_order->drivers.push_back(one);
        new_driver_index = (int)(pool_order->drivers.size() - 1);
      } else {
        VLOG(4) << "old driver phone " << did;
        new_driver_index = -1;
      }
    } else {
      int priority = StringToInt(did);
      if (new_driver_index >= 0) {
        VLOG(4) << "new driver priority " << priority << ", index=" << new_driver_index;
        pool_order->drivers[new_driver_index].priority = priority;
        new_driver_index = -1;
      } else {
        VLOG(4) << "old driver priority " << priority;
      }
    }

  }


  if (pool_order->drivers.size() > 0) {
    // send message, update pushtime:
    VLOG(2) << "send message: " << pool_order->id;
    SendMessage(pool_order);

    // record new history drivers
    VLOG(2) << "record new history drivers for " << pool_order->id;
    for (size_t i = 0; i < pool_order->drivers.size(); ++i) {
      hd.drivers.insert(pool_order->drivers[i].phone);
    }
    hd.update_time = GetTimeInSec();
    
    std::string hdstr = ThriftToString(&hd);
    history_driver_rm_.Set(pool_id, hdstr);

  } else {
    // no new drivers available
    VLOG(2) << "no new drivers available for " << pool_order->id;
  
    // check if timeout, clear history driver and re-send
    int64_t duration = base::GetTimeInSec() - hd.update_time;
    if (FLAGS_schedule_restart_period > 1 &&
        duration > FLAGS_schedule_restart_period) {
      VLOG(2) << "clear history driver and re-start sending loop";
      history_driver_rm_.Del(pool_id);
    }

  }
   
  // send to re-pack queue
  VLOG(2) << "put to repacker queue";
  pool_order->pushtime = GetTimeInMs();
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
  msg.template_type = 1;  // notification template
  msg.push_type = 1;  // to list
  msg.app_type = 1; // to driver
  msg.title = "poolorder";
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
