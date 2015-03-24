#include <iostream>
#include <boost/unordered_map.hpp>
#include "gen-cpp/order_types.h"
#include "base/time.h"

using namespace std;
using namespace base;
using namespace scheduler;


int main(int argc, char* argv[]) {
  cout << base::GetTimeInSec() << endl;
  return 0;
}
