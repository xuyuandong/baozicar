
#include "repacker.h"
#include "order_types.h"
#include "base/time.h"
#include "base/string_util.h"

DEFINE_int32(schedule_send_period, 5000, "milli-second period for scheduler send a pool order");
DEFINE_int32(sleep_msec_repacker, 5000, "sleep time in milli-seconds when scheduler is waiting");

using namespace base;

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

    base::MilliSleep(FLAGS_sleep_msec_repacker);
  }

}

void Repacker::CheckAndWait(PoolOrder* pool_order) {
  // wait period time - 1s
  int duration = FLAGS_schedule_send_period - (int)(GetTimeInMs() - pool_order->pushtime);
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

  if (flag) {  // delete carpool id  
    carpool_rmq_.Del(pool_order->id);
   // put not canceled order back to order map queue
    for (size_t i = 0; i < orders.size(); ++i) {
      order_rmq_.PutKey(orders[i]);
    }
  } else {  // put back to carpool map queue
    carpool_rmq_.PutKey(pool_order->id);
  }

}

}  // end namespace
