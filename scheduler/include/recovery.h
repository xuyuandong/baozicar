#ifndef _RECOVERY_H_
#define _RECOVERY_H_

#include "redispp.h"
#include "thrift.h"

namespace scheduler {

class Recovery {
  public:
    Recovery(const std::string& host, int port) 
      :redis_(host.c_str(), port) {}
    ~Recovery() {}

    void SetRedis(const std::string& order_rmq, 
        const std::string& pooler_rmq) {
      lorder_ = "l_" + order_rmq;
      horder_ = "h_" + order_rmq;
      lpooler_ = "l_" + pooler_rmq;
      hpooler_ = "h_" + pooler_rmq;
    }

    void Do();

  private:
    base::Redispp redis_;
    base::ThriftTool thrift_;
    
    std::string lorder_;
    std::string horder_;
    std::string lpooler_;
    std::string hpooler_;

  DISALLOW_COPY_AND_ASSIGN(Recovery);
};

}  // end namespace

#endif  // _RECOVERY_H_
