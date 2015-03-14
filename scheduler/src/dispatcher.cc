
#include "dispatcher.h"
#include "order_types.h"

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
    
    usleep(100000);
  }
}



}  // end namespace
