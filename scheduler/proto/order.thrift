namespace py scheduler
namespace cpp scheduler
namespace java scheduler

struct Path {
  1: string from_city,
  2: string from_place,
  3: string to_city,
  4: string to_place,
  5: double from_lat,
  6: double from_lng,
  7: double to_lat,
  8: double to_lng
}

struct Order {
  1: i64 id,
  2: Path path,
  3: string phone,
  4: i32 number,
  5: i32 cartype,
  6: double price,
  7: i64 time
}

struct Driver {
  1: string phone,
  2: i32 priority
}

struct HistoryDriver {
  1: set<string> drivers
}

struct PoolOrder {
  1: string id,
  2: i32 cartype,
  3: list<Order> order_list,
  4: i64 pushtime,
  5: list<Driver> drivers,
  6: double subsidy = 0.0,
  7: i32 sstype = 0,
  8: i32 number
}

struct Message {
  1: i32 template_type,
  2: i32 push_type,
  3: i32 app_type,
  4: string title,
  5: string content,
  6: string text,
  7: string url,
  8: list<string> target
}
