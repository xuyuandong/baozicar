#include "stations.h"
#include <cmath>
#include <algorithm>
#include "order_types.h"
#include "base/string_util.h"
#include "base/time.h"

DEFINE_int32(station_cache_expire_time, 3600, "expire time in seconds for station cache re-read redis");
DEFINE_string(station_rset, "station", "redis set for path stations");


namespace scheduler {

void StationManager::Init(base::Redispp* redis) {
  rset_.Init(redis, FLAGS_station_rset);
  station_cache_.SetExpireTime(FLAGS_station_cache_expire_time);
}

void StationManager::FetchStations(const Order* order, std::vector<std::string>* stations) {
  VLOG(4) << "fetch stations " << order->path.from_city << " " << order->path.to_city;
  stations->clear();
  
  Station src;
  src.name_ = order->path.from_city;
  src.lng_ = order->path.from_lng;
  src.lat_ = order->path.from_lat;

  std::string from_station;
  if (GetNearestStation(src, &from_station)) {
    stations->push_back(from_station);
  } else {
    stations->push_back(order->path.from_city);
  }

  Station dst;
  dst.name_ = order->path.to_city;
  dst.lng_ = order->path.to_lng;
  dst.lat_ = order->path.to_lat;

  std::string to_station;
  if (GetNearestStation(dst, &to_station)) {
    stations->push_back(to_station);
  } else {
    stations->push_back(order->path.to_city);
  }
}

bool StationManager::GetNearestStation(const Station& city, std::string* station) {
  VLOG(4) << "get all stations for " << city.name_;
  std::vector<Station> station_vec;
  GetAllStations(city.name_, &station_vec);
 
  VLOG(4) << "calculate nearest station " << city.name_;
  if (station_vec.size() > 0) {
    double min_dist = 10000.0;
    for (size_t i = 0; i < station_vec.size(); ++i) {
      double dist = CalcDistance(city.lng_, city.lat_, station_vec[i].lng_, station_vec[i].lat_);
      if (min_dist > dist) {
        min_dist = dist;
        *station = station_vec[i].name_;
      }
    }
    return true;
  } 
  return false;
}

void StationManager::GetAllStations(const std::string& city, std::vector<Station>* stations) {
  VLOG(5) << "fetch station cache";
  if (station_cache_.Fetch(city, stations)) {
    return;
  } 

  // fetch redis
  VLOG(5) << "fetch station redis";
  stations->clear();
  base::ReplyObj t;
  t = rset_.GetAll(city);

  if (t.OK() && t.Num() > 0) {
    VLOG(5) << "find " << city << " station record " << t.Num();
    for (size_t i = 0; i < t.Num(); ++i) {
      std::string line(t.Ele(i)->str);
      std::vector<std::string> result;
      SplitString(line, ' ', &result);
      
      int idx = 0;
      Station tmp;
      for (size_t j = 0; j < result.size(); ++j) {
        if (result[j].size() == 0)
          continue;

        switch (idx) {
        case 0:
          tmp.name_ = result[j];
          break;
        case 1:
          tmp.lng_ = StringToDouble(result[j]);
          break;
        case 2:
          tmp.lat_ = StringToDouble(result[j]);
          break;
        default:
          break;
        }
        idx += 1;
      }
      if (idx == 3) {
        stations->push_back(tmp);
      } else {
        VLOG(2) << "bad record: "<< line;
      }
    }
  } else {
    VLOG(2) << "no station for " << city;
  }

  // write to cache
  station_cache_.Write(city, *stations);
}

double StationManager::CalcDistance(double lng1, double lat1, double lng2, double lat2) {
  double a = lng1 - lng2;
  double b = lat1 - lat2;
  return 100 * sqrt(a*a + b*b);
}




}  // end namespace
