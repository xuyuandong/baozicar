
#include "revoker.h"
#include "order_types.h"
#include "base/string_util.h"

DEFINE_int32(sleep_msec_revoker, 5000, "sleep time in milli-seconds when scheduler is waiting");

namespace scheduler {

void Revoker::Run() {
  while(true) {
    
    while (!queue_->Empty()) {
      Order* order = NULL;
      queue_->Pop(order);

      if (order == NULL) {
        VLOG(2) << "FOUND NULL ORDER";
        continue;
      }

      const std::string& key = Int64ToString(order->id);
      VLOG(2) << "check order " << key;

      if (rmq_.Check(key) > 0) {
        // put back not-cancelled order to redis queue
        rmq_.PutKey(key);
      }

      // release order memory
      delete order;
      order = NULL;
    }

    VLOG(5) << "revoker sleep " << FLAGS_sleep_msec_revoker << " msec";
    base::MilliSleep(FLAGS_sleep_msec_revoker);
  }
}

}  // end namespace
