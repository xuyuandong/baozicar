#include <signal.h>
#include "base/flags.h"
#include "base/logging.h"
#include "base/concurrent_queue.h"

#include "dispatcher.h"
#include "carpooler.h"
#include "revoker.h"
#include "planner.h"
#include "repacker.h"
#include "recovery.h"

using namespace base;
using namespace logging;
using namespace scheduler;

DEFINE_string(log_file, "main.log", "program log file");
DEFINE_string(host, "localhost", "redis server listen host");
DEFINE_int32(port, 6379, "redis server listen port");

DEFINE_string(order_rmq, "orders", "redis map queue for incoming orders");
DEFINE_string(carpool_rmq, "carpools", "redis map queue for carpool orders");
DEFINE_string(message_rq, "messages", "redis message queue for pushing");
DEFINE_string(driver_rpq, "drivers", "redis zset for path-driver selection");
DEFINE_string(path_rsm, "path", "redis zset for path-driver selection");
DEFINE_string(history_driver_rm, "history_driver", "redis map for order - history drivers");

int main(int argc, char* argv[]) {
  ParseCommandLineFlags(&argc, &argv, true);
  //InitLogging(FLAGS_log_file.c_str(), LOG_ONLY_TO_FILE, LOCK_LOG_FILE, APPEND_TO_OLD_LOG_FILE);

  signal(SIGPIPE, SIG_IGN);

  // order pipeline
  ConcurrentQueue<Order*>* order_queue = new ConcurrentQueue<Order*>();
  ConcurrentQueue<Order*>* left_order_queue = new ConcurrentQueue<Order*>();
  
  Dispatcher dispatcher(FLAGS_host, FLAGS_port);
  dispatcher.SetupInputRedis(FLAGS_order_rmq);
  dispatcher.SetupOutputQueue(order_queue);

  Carpooler carpooler(FLAGS_host, FLAGS_port);
  carpooler.SetupPathRedis(FLAGS_path_rsm);
  carpooler.SetupOutputRedis(FLAGS_carpool_rmq);
  carpooler.SetupQueue(order_queue, left_order_queue);

  Revoker revoker(FLAGS_host, FLAGS_port);
  revoker.SetupInputQueue(left_order_queue);
  revoker.SetupOutputRedis(FLAGS_order_rmq);

  // pool order pipeline
  ConcurrentQueue<PoolOrder*>* pool_order_queue = new ConcurrentQueue<PoolOrder*>();

  Planner planner(FLAGS_host, FLAGS_port);
  planner.SetupInputRedis(FLAGS_carpool_rmq);
  planner.SetupOutputRedis(FLAGS_message_rq);
  planner.SetupAssitRedis(FLAGS_driver_rpq, FLAGS_history_driver_rm);
  planner.SetupOutputQueue(pool_order_queue);

  Repacker repacker(FLAGS_host, FLAGS_port);
  repacker.SetupInputQueue(pool_order_queue);
  repacker.SetupOutputRedis(FLAGS_carpool_rmq);
  repacker.SetupCheckRedis(FLAGS_order_rmq);

  // recover
  Recovery recovery(FLAGS_host, FLAGS_port);
  recovery.SetRedis(FLAGS_order_rmq, FLAGS_carpool_rmq);
  recovery.Do();
  LOG(INFO) << "finished recovery";

  // start order pipeline
  revoker.Start();
  LOG(INFO) << "started revoker";
  carpooler.Start();
  LOG(INFO) << "started carpooler";
  dispatcher.Start();
  LOG(INFO) << "started dispatcher";

  // start pool order pipeline
  repacker.Start();
  LOG(INFO) << "started repacker";
  planner.Start();
  LOG(INFO) << "started planner";
  
  // wait finished
  while (1) {
    sleep(10);
  }

  return 0;
}
