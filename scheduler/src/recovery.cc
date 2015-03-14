
#include <set>
#include <vector>
#include "recovery.h"
#include "order_types.h"
#include "base/string_util.h"

namespace scheduler {

void Recovery::Do() {
  std::vector<std::string> poolids_;
  std::vector<std::string> orderids_;
  std::set<std::string> poolorderids_;

  base::ReplyObj t;
  base::Redispp* r_ = &this->redis_;

  // get pool ids from hash map
  t = r_->execute("HKEYS %s", hpooler_.c_str());
  if (t.OK() && t.Num() > 0) {
    for (size_t i = 0; i < t.Num(); ++i) {
      poolids_.push_back(t.Ele(i)->str);
    }
  }

  // push pool ids to pool list
  t = r_->execute("DEL %s", lpooler_.c_str());
  for (size_t i = 0; i < poolids_.size(); ++i) {
    t = r_->execute("LPUSH %s %s", lpooler_.c_str(), poolids_[i].c_str());
  }

  // get pool order ids from pool hash map
  for (size_t i = 0; i < poolids_.size(); ++i) {
    t = r_->execute("HGET %s %s", hpooler_.c_str(), poolids_[i].c_str());
    std::string str(t.Str(), t.Len());
    PoolOrder* po = new PoolOrder();
    if (thrift_.StringToThrift(str, po)) {
      for (size_t i = 0; i < po->order_list.size(); ++i) {
        std::string order_id = Int64ToString(po->order_list[i].id);
        poolorderids_.insert(order_id);    
      }
    }
    delete po;
  }

  // get all order ids from order hash map
  t = r_->execute("HKEYS %s", horder_.c_str());
  if (t.OK() && t.Num() > 0) {
    for (size_t i = 0; i < t.Num(); ++i) {
      orderids_.push_back(t.Ele(i)->str);
    }
  }

  // push order ids (exclude in pool order ids) to order list
  t = r_->execute("DEL %s", lorder_.c_str());
  for (size_t i = 0; i < orderids_.size(); ++i) {
    if (poolorderids_.find(orderids_[i]) == poolorderids_.end()) {
      t = r_->execute("LPUSH %s %s", lorder_.c_str(), orderids_[i].c_str());
    }
  }

}

}// end namespace
