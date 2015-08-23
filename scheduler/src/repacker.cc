
#include "repacker.h"
#include "order_types.h"
#include "base/time.h"
#include "base/string_util.h"

DEFINE_int32(schedule_send_period, 5000, "milli-second period for scheduler send a pool order");
DEFINE_int32(sleep_msec_repacker, 5000, "sleep time in milli-seconds when scheduler is waiting");
DEFINE_int32(poolorder_life_period, 100000, "life period is over, poolorder will not pushed to drivers");
DEFINE_int32(wait_confirm_time, 50, "milli-second time for waiting web engine server to confirm a poolorder");

namespace scheduler {

void Repacker::Run() {
  while (true) {

    while (!queue_->Empty()) {
      PoolOrder* pool_order = NULL;
      queue_->Pop(pool_order);

      VLOG(2) << "check wait poolorder " << pool_order->id;
      CheckAndWait(pool_order);

      delete pool_order;
      pool_order = NULL;
    }

    VLOG(5) << "repacker sleep " << FLAGS_sleep_msec_repacker << " msec";
    base::MilliSleep(FLAGS_sleep_msec_repacker);
  }

}

void Repacker::CheckAndWait(PoolOrder* pool_order) {
  int64_t current_time = base::GetTimeInMs();
  // check life period by birthday
  if (pool_order->__isset.birthday) {
    int life = (int)(current_time / 1000 - pool_order->birthday);
    if (life > FLAGS_poolorder_life_period) {
      LOG(INFO) << "PoolOrder id=" << pool_order->id << " stops its life period";
      carpool_rmq_.Del(pool_order->id);
      history_driver_rm_.Del(pool_order->id);
      return;
    }
  }
  
  // wait period time - 1s
  int duration = FLAGS_schedule_send_period - (int)(current_time - pool_order->pushtime);
  if (duration > 0) {
    base::MilliSleep(duration);
  }

  // check cancel or done
  bool flag = false;
  std::vector<std::string> orders;

  for (size_t i = 0; i < pool_order->order_list.size(); ++i) {
    const std::string oid = Int64ToString(pool_order->order_list[i].id);
    if (1 > order_rmq_.Check(oid)) {  // cancel or confirm
      flag = true;  
    } else {  // not cancel
      orders.push_back(oid);
    }
  }

  if (flag) { // poolorder is canceled or confirmed
    
   // put not canceled order back to order map queue
    for (size_t i = 0; i < orders.size(); ++i) {
      order_rmq_.PutKey(orders[i]);
    }
    // delete carpool id  
    base::MilliSleep(FLAGS_wait_confirm_time);
    carpool_rmq_.Del(pool_order->id);
    history_driver_rm_.Del(pool_order->id);

  } else {  // put back to carpool map queue
    carpool_rmq_.PutKey(pool_order->id);
  }

}

}  // end namespace
