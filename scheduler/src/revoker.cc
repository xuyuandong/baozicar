
#include "revoker.h"
#include "order_types.h"
#include "base/string_util.h"

namespace scheduler {

void Revoker::Run() {
  while(true) {
    
    while (!queue_->Empty()) {
      Order* order = NULL;
      queue_->Pop(order);
      
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

  }
}

}  // end namespace
