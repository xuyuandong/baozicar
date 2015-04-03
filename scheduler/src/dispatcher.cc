
#include "dispatcher.h"
#include "order_types.h"

DEFINE_int32(sleep_msec_dispatcher, 5000, "sleep time in milli-seconds when scheduler is waiting");

using namespace base;

namespace scheduler {

void Dispatcher::Run() {
  while (!stop_) {

    while (rmq_.Len() > 0) {
      ReplyObj robj;
      robj = rmq_.Pop();
      
      if (robj.OK()) {
        std::string str(robj.Str(), robj.Len());

        Order* order = new Order();
        if (thrift_.StringToThrift(str, order)) {
          VLOG(2) << "push order: " << order->id;
          queue_->Push(order);
        } else {
          //TODO: how to deal with?
          delete order;
        }
      }

    } 
    
    VLOG(5) << "dispatcher sleep " << FLAGS_sleep_msec_dispatcher << " msec";
    base::MilliSleep(FLAGS_sleep_msec_dispatcher);
  }
}



}  // end namespace
