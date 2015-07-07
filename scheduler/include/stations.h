#ifndef _STATIONS_H_
#define _STATIONS_H_

#include <map>
#include <vector>
#include <boost/unordered_map.hpp>
#include "redispp.h"

namespace scheduler {

class Order;

struct Station {
  std::string name_;
  double lng_;
  double lat_;
};

class StationManager {
  public:
    void Init(base::Redispp* redis);
    // return nearest from_station and to_station
    void FetchStations(const Order* order, std::vector<std::string>* stations);

  private:
    bool GetNearestStation(const Station& city, std::string* station);
    void GetAllStations(const std::string& city, std::vector<Station>* stations);
    double CalcDistance(double lng1, double lat1, double lng2, double lat2);

  private:
    std::map<std::string, std::vector<Station> > cache_;
    int64_t cache_timestamp_;
    base::RedisSet rset_;

};


}  // end namespace

#endif  // _STATIONS_H_
