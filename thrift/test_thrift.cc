#include <iostream>
#include <hiredis.h>
#include <boost/unordered_map.hpp>
#include "thrift.h"
#include "gen-cpp/order_types.h"
#include "redisv.h"

using namespace base;
using namespace scheduler;


int main(int argc, char* argv[]) {
  base::Redispp rpp("127.0.0.1", 6379);

  base::RedisMapQueue queue(&rpp, "order");



  ThriftTool tt;
  Order* neworder = new Order();
  if (tt.StringToThrift(mystr, neworder)) {
    std::cout << neworder->booktime << std::endl;
  } else {
    std::cout << "failed" << std::endl;
  }
 
  std::cout << queue.Len() << std::endl;
  std::cout << queue.Check("one") << std::endl;
  queue.Put("one", mystr);
  for (int i = 0; i < 10; i++) {
    res = queue.Pop();
    if (!res.OK()) {
      std::cout << "pop " << i << std::endl;
    }
  }
  std::cout << queue.Check("one") << std::endl;

  std::cout << queue.Len() << std::endl;
  std::cout << queue.Size() << std::endl;

  return 0;
}
