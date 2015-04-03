/**
 * Autogenerated by Thrift Compiler (1.0.0-dev)
 *
 * DO NOT EDIT UNLESS YOU ARE SURE THAT YOU KNOW WHAT YOU ARE DOING
 *  @generated
 */
#include "order_types.h"

#include <algorithm>
#include <ostream>

#include <thrift/TToString.h>

namespace scheduler {


Path::~Path() throw() {
}


void Path::__set_from_city(const std::string& val) {
  this->from_city = val;
}

void Path::__set_from_place(const std::string& val) {
  this->from_place = val;
}

void Path::__set_to_city(const std::string& val) {
  this->to_city = val;
}

void Path::__set_to_place(const std::string& val) {
  this->to_place = val;
}

void Path::__set_from_lat(const double val) {
  this->from_lat = val;
}

void Path::__set_from_lng(const double val) {
  this->from_lng = val;
}

void Path::__set_to_lat(const double val) {
  this->to_lat = val;
}

void Path::__set_to_lng(const double val) {
  this->to_lng = val;
}

const char* Path::ascii_fingerprint = "245F00F9E4A5B0CEA9EB39A7B2A82616";
const uint8_t Path::binary_fingerprint[16] = {0x24,0x5F,0x00,0xF9,0xE4,0xA5,0xB0,0xCE,0xA9,0xEB,0x39,0xA7,0xB2,0xA8,0x26,0x16};

uint32_t Path::read(::apache::thrift::protocol::TProtocol* iprot) {

  uint32_t xfer = 0;
  std::string fname;
  ::apache::thrift::protocol::TType ftype;
  int16_t fid;

  xfer += iprot->readStructBegin(fname);

  using ::apache::thrift::protocol::TProtocolException;


  while (true)
  {
    xfer += iprot->readFieldBegin(fname, ftype, fid);
    if (ftype == ::apache::thrift::protocol::T_STOP) {
      break;
    }
    switch (fid)
    {
      case 1:
        if (ftype == ::apache::thrift::protocol::T_STRING) {
          xfer += iprot->readString(this->from_city);
          this->__isset.from_city = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 2:
        if (ftype == ::apache::thrift::protocol::T_STRING) {
          xfer += iprot->readString(this->from_place);
          this->__isset.from_place = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 3:
        if (ftype == ::apache::thrift::protocol::T_STRING) {
          xfer += iprot->readString(this->to_city);
          this->__isset.to_city = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 4:
        if (ftype == ::apache::thrift::protocol::T_STRING) {
          xfer += iprot->readString(this->to_place);
          this->__isset.to_place = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 5:
        if (ftype == ::apache::thrift::protocol::T_DOUBLE) {
          xfer += iprot->readDouble(this->from_lat);
          this->__isset.from_lat = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 6:
        if (ftype == ::apache::thrift::protocol::T_DOUBLE) {
          xfer += iprot->readDouble(this->from_lng);
          this->__isset.from_lng = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 7:
        if (ftype == ::apache::thrift::protocol::T_DOUBLE) {
          xfer += iprot->readDouble(this->to_lat);
          this->__isset.to_lat = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 8:
        if (ftype == ::apache::thrift::protocol::T_DOUBLE) {
          xfer += iprot->readDouble(this->to_lng);
          this->__isset.to_lng = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      default:
        xfer += iprot->skip(ftype);
        break;
    }
    xfer += iprot->readFieldEnd();
  }

  xfer += iprot->readStructEnd();

  return xfer;
}

uint32_t Path::write(::apache::thrift::protocol::TProtocol* oprot) const {
  uint32_t xfer = 0;
  oprot->incrementRecursionDepth();
  xfer += oprot->writeStructBegin("Path");

  xfer += oprot->writeFieldBegin("from_city", ::apache::thrift::protocol::T_STRING, 1);
  xfer += oprot->writeString(this->from_city);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("from_place", ::apache::thrift::protocol::T_STRING, 2);
  xfer += oprot->writeString(this->from_place);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("to_city", ::apache::thrift::protocol::T_STRING, 3);
  xfer += oprot->writeString(this->to_city);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("to_place", ::apache::thrift::protocol::T_STRING, 4);
  xfer += oprot->writeString(this->to_place);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("from_lat", ::apache::thrift::protocol::T_DOUBLE, 5);
  xfer += oprot->writeDouble(this->from_lat);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("from_lng", ::apache::thrift::protocol::T_DOUBLE, 6);
  xfer += oprot->writeDouble(this->from_lng);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("to_lat", ::apache::thrift::protocol::T_DOUBLE, 7);
  xfer += oprot->writeDouble(this->to_lat);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("to_lng", ::apache::thrift::protocol::T_DOUBLE, 8);
  xfer += oprot->writeDouble(this->to_lng);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldStop();
  xfer += oprot->writeStructEnd();
  oprot->decrementRecursionDepth();
  return xfer;
}

void swap(Path &a, Path &b) {
  using ::std::swap;
  swap(a.from_city, b.from_city);
  swap(a.from_place, b.from_place);
  swap(a.to_city, b.to_city);
  swap(a.to_place, b.to_place);
  swap(a.from_lat, b.from_lat);
  swap(a.from_lng, b.from_lng);
  swap(a.to_lat, b.to_lat);
  swap(a.to_lng, b.to_lng);
  swap(a.__isset, b.__isset);
}

Path::Path(const Path& other0) {
  from_city = other0.from_city;
  from_place = other0.from_place;
  to_city = other0.to_city;
  to_place = other0.to_place;
  from_lat = other0.from_lat;
  from_lng = other0.from_lng;
  to_lat = other0.to_lat;
  to_lng = other0.to_lng;
  __isset = other0.__isset;
}
Path& Path::operator=(const Path& other1) {
  from_city = other1.from_city;
  from_place = other1.from_place;
  to_city = other1.to_city;
  to_place = other1.to_place;
  from_lat = other1.from_lat;
  from_lng = other1.from_lng;
  to_lat = other1.to_lat;
  to_lng = other1.to_lng;
  __isset = other1.__isset;
  return *this;
}
std::ostream& operator<<(std::ostream& out, const Path& obj) {
  using apache::thrift::to_string;
  out << "Path(";
  out << "from_city=" << to_string(obj.from_city);
  out << ", " << "from_place=" << to_string(obj.from_place);
  out << ", " << "to_city=" << to_string(obj.to_city);
  out << ", " << "to_place=" << to_string(obj.to_place);
  out << ", " << "from_lat=" << to_string(obj.from_lat);
  out << ", " << "from_lng=" << to_string(obj.from_lng);
  out << ", " << "to_lat=" << to_string(obj.to_lat);
  out << ", " << "to_lng=" << to_string(obj.to_lng);
  out << ")";
  return out;
}


Order::~Order() throw() {
}


void Order::__set_id(const int64_t val) {
  this->id = val;
}

void Order::__set_path(const Path& val) {
  this->path = val;
}

void Order::__set_phone(const std::string& val) {
  this->phone = val;
}

void Order::__set_number(const int32_t val) {
  this->number = val;
}

void Order::__set_cartype(const int32_t val) {
  this->cartype = val;
}

void Order::__set_price(const double val) {
  this->price = val;
}

void Order::__set_time(const int64_t val) {
  this->time = val;
}

const char* Order::ascii_fingerprint = "0E95B2698AD9772974A275159CF76313";
const uint8_t Order::binary_fingerprint[16] = {0x0E,0x95,0xB2,0x69,0x8A,0xD9,0x77,0x29,0x74,0xA2,0x75,0x15,0x9C,0xF7,0x63,0x13};

uint32_t Order::read(::apache::thrift::protocol::TProtocol* iprot) {

  uint32_t xfer = 0;
  std::string fname;
  ::apache::thrift::protocol::TType ftype;
  int16_t fid;

  xfer += iprot->readStructBegin(fname);

  using ::apache::thrift::protocol::TProtocolException;


  while (true)
  {
    xfer += iprot->readFieldBegin(fname, ftype, fid);
    if (ftype == ::apache::thrift::protocol::T_STOP) {
      break;
    }
    switch (fid)
    {
      case 1:
        if (ftype == ::apache::thrift::protocol::T_I64) {
          xfer += iprot->readI64(this->id);
          this->__isset.id = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 2:
        if (ftype == ::apache::thrift::protocol::T_STRUCT) {
          xfer += this->path.read(iprot);
          this->__isset.path = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 3:
        if (ftype == ::apache::thrift::protocol::T_STRING) {
          xfer += iprot->readString(this->phone);
          this->__isset.phone = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 4:
        if (ftype == ::apache::thrift::protocol::T_I32) {
          xfer += iprot->readI32(this->number);
          this->__isset.number = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 5:
        if (ftype == ::apache::thrift::protocol::T_I32) {
          xfer += iprot->readI32(this->cartype);
          this->__isset.cartype = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 6:
        if (ftype == ::apache::thrift::protocol::T_DOUBLE) {
          xfer += iprot->readDouble(this->price);
          this->__isset.price = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 7:
        if (ftype == ::apache::thrift::protocol::T_I64) {
          xfer += iprot->readI64(this->time);
          this->__isset.time = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      default:
        xfer += iprot->skip(ftype);
        break;
    }
    xfer += iprot->readFieldEnd();
  }

  xfer += iprot->readStructEnd();

  return xfer;
}

uint32_t Order::write(::apache::thrift::protocol::TProtocol* oprot) const {
  uint32_t xfer = 0;
  oprot->incrementRecursionDepth();
  xfer += oprot->writeStructBegin("Order");

  xfer += oprot->writeFieldBegin("id", ::apache::thrift::protocol::T_I64, 1);
  xfer += oprot->writeI64(this->id);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("path", ::apache::thrift::protocol::T_STRUCT, 2);
  xfer += this->path.write(oprot);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("phone", ::apache::thrift::protocol::T_STRING, 3);
  xfer += oprot->writeString(this->phone);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("number", ::apache::thrift::protocol::T_I32, 4);
  xfer += oprot->writeI32(this->number);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("cartype", ::apache::thrift::protocol::T_I32, 5);
  xfer += oprot->writeI32(this->cartype);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("price", ::apache::thrift::protocol::T_DOUBLE, 6);
  xfer += oprot->writeDouble(this->price);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("time", ::apache::thrift::protocol::T_I64, 7);
  xfer += oprot->writeI64(this->time);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldStop();
  xfer += oprot->writeStructEnd();
  oprot->decrementRecursionDepth();
  return xfer;
}

void swap(Order &a, Order &b) {
  using ::std::swap;
  swap(a.id, b.id);
  swap(a.path, b.path);
  swap(a.phone, b.phone);
  swap(a.number, b.number);
  swap(a.cartype, b.cartype);
  swap(a.price, b.price);
  swap(a.time, b.time);
  swap(a.__isset, b.__isset);
}

Order::Order(const Order& other2) {
  id = other2.id;
  path = other2.path;
  phone = other2.phone;
  number = other2.number;
  cartype = other2.cartype;
  price = other2.price;
  time = other2.time;
  __isset = other2.__isset;
}
Order& Order::operator=(const Order& other3) {
  id = other3.id;
  path = other3.path;
  phone = other3.phone;
  number = other3.number;
  cartype = other3.cartype;
  price = other3.price;
  time = other3.time;
  __isset = other3.__isset;
  return *this;
}
std::ostream& operator<<(std::ostream& out, const Order& obj) {
  using apache::thrift::to_string;
  out << "Order(";
  out << "id=" << to_string(obj.id);
  out << ", " << "path=" << to_string(obj.path);
  out << ", " << "phone=" << to_string(obj.phone);
  out << ", " << "number=" << to_string(obj.number);
  out << ", " << "cartype=" << to_string(obj.cartype);
  out << ", " << "price=" << to_string(obj.price);
  out << ", " << "time=" << to_string(obj.time);
  out << ")";
  return out;
}


Driver::~Driver() throw() {
}


void Driver::__set_phone(const std::string& val) {
  this->phone = val;
}

void Driver::__set_priority(const int32_t val) {
  this->priority = val;
}

const char* Driver::ascii_fingerprint = "EEBC915CE44901401D881E6091423036";
const uint8_t Driver::binary_fingerprint[16] = {0xEE,0xBC,0x91,0x5C,0xE4,0x49,0x01,0x40,0x1D,0x88,0x1E,0x60,0x91,0x42,0x30,0x36};

uint32_t Driver::read(::apache::thrift::protocol::TProtocol* iprot) {

  uint32_t xfer = 0;
  std::string fname;
  ::apache::thrift::protocol::TType ftype;
  int16_t fid;

  xfer += iprot->readStructBegin(fname);

  using ::apache::thrift::protocol::TProtocolException;


  while (true)
  {
    xfer += iprot->readFieldBegin(fname, ftype, fid);
    if (ftype == ::apache::thrift::protocol::T_STOP) {
      break;
    }
    switch (fid)
    {
      case 1:
        if (ftype == ::apache::thrift::protocol::T_STRING) {
          xfer += iprot->readString(this->phone);
          this->__isset.phone = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 2:
        if (ftype == ::apache::thrift::protocol::T_I32) {
          xfer += iprot->readI32(this->priority);
          this->__isset.priority = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      default:
        xfer += iprot->skip(ftype);
        break;
    }
    xfer += iprot->readFieldEnd();
  }

  xfer += iprot->readStructEnd();

  return xfer;
}

uint32_t Driver::write(::apache::thrift::protocol::TProtocol* oprot) const {
  uint32_t xfer = 0;
  oprot->incrementRecursionDepth();
  xfer += oprot->writeStructBegin("Driver");

  xfer += oprot->writeFieldBegin("phone", ::apache::thrift::protocol::T_STRING, 1);
  xfer += oprot->writeString(this->phone);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("priority", ::apache::thrift::protocol::T_I32, 2);
  xfer += oprot->writeI32(this->priority);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldStop();
  xfer += oprot->writeStructEnd();
  oprot->decrementRecursionDepth();
  return xfer;
}

void swap(Driver &a, Driver &b) {
  using ::std::swap;
  swap(a.phone, b.phone);
  swap(a.priority, b.priority);
  swap(a.__isset, b.__isset);
}

Driver::Driver(const Driver& other4) {
  phone = other4.phone;
  priority = other4.priority;
  __isset = other4.__isset;
}
Driver& Driver::operator=(const Driver& other5) {
  phone = other5.phone;
  priority = other5.priority;
  __isset = other5.__isset;
  return *this;
}
std::ostream& operator<<(std::ostream& out, const Driver& obj) {
  using apache::thrift::to_string;
  out << "Driver(";
  out << "phone=" << to_string(obj.phone);
  out << ", " << "priority=" << to_string(obj.priority);
  out << ")";
  return out;
}


HistoryDriver::~HistoryDriver() throw() {
}


void HistoryDriver::__set_drivers(const std::set<std::string> & val) {
  this->drivers = val;
}

void HistoryDriver::__set_reduced(const bool val) {
  this->reduced = val;
}

void HistoryDriver::__set_update_time(const int64_t val) {
  this->update_time = val;
}

const char* HistoryDriver::ascii_fingerprint = "386F45436DBA0A499AA232A1080C0B92";
const uint8_t HistoryDriver::binary_fingerprint[16] = {0x38,0x6F,0x45,0x43,0x6D,0xBA,0x0A,0x49,0x9A,0xA2,0x32,0xA1,0x08,0x0C,0x0B,0x92};

uint32_t HistoryDriver::read(::apache::thrift::protocol::TProtocol* iprot) {

  uint32_t xfer = 0;
  std::string fname;
  ::apache::thrift::protocol::TType ftype;
  int16_t fid;

  xfer += iprot->readStructBegin(fname);

  using ::apache::thrift::protocol::TProtocolException;


  while (true)
  {
    xfer += iprot->readFieldBegin(fname, ftype, fid);
    if (ftype == ::apache::thrift::protocol::T_STOP) {
      break;
    }
    switch (fid)
    {
      case 1:
        if (ftype == ::apache::thrift::protocol::T_SET) {
          {
            this->drivers.clear();
            uint32_t _size6;
            ::apache::thrift::protocol::TType _etype9;
            xfer += iprot->readSetBegin(_etype9, _size6);
            uint32_t _i10;
            for (_i10 = 0; _i10 < _size6; ++_i10)
            {
              std::string _elem11;
              xfer += iprot->readString(_elem11);
              this->drivers.insert(_elem11);
            }
            xfer += iprot->readSetEnd();
          }
          this->__isset.drivers = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 2:
        if (ftype == ::apache::thrift::protocol::T_BOOL) {
          xfer += iprot->readBool(this->reduced);
          this->__isset.reduced = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 3:
        if (ftype == ::apache::thrift::protocol::T_I64) {
          xfer += iprot->readI64(this->update_time);
          this->__isset.update_time = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      default:
        xfer += iprot->skip(ftype);
        break;
    }
    xfer += iprot->readFieldEnd();
  }

  xfer += iprot->readStructEnd();

  return xfer;
}

uint32_t HistoryDriver::write(::apache::thrift::protocol::TProtocol* oprot) const {
  uint32_t xfer = 0;
  oprot->incrementRecursionDepth();
  xfer += oprot->writeStructBegin("HistoryDriver");

  xfer += oprot->writeFieldBegin("drivers", ::apache::thrift::protocol::T_SET, 1);
  {
    xfer += oprot->writeSetBegin(::apache::thrift::protocol::T_STRING, static_cast<uint32_t>(this->drivers.size()));
    std::set<std::string> ::const_iterator _iter12;
    for (_iter12 = this->drivers.begin(); _iter12 != this->drivers.end(); ++_iter12)
    {
      xfer += oprot->writeString((*_iter12));
    }
    xfer += oprot->writeSetEnd();
  }
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("reduced", ::apache::thrift::protocol::T_BOOL, 2);
  xfer += oprot->writeBool(this->reduced);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("update_time", ::apache::thrift::protocol::T_I64, 3);
  xfer += oprot->writeI64(this->update_time);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldStop();
  xfer += oprot->writeStructEnd();
  oprot->decrementRecursionDepth();
  return xfer;
}

void swap(HistoryDriver &a, HistoryDriver &b) {
  using ::std::swap;
  swap(a.drivers, b.drivers);
  swap(a.reduced, b.reduced);
  swap(a.update_time, b.update_time);
  swap(a.__isset, b.__isset);
}

HistoryDriver::HistoryDriver(const HistoryDriver& other13) {
  drivers = other13.drivers;
  reduced = other13.reduced;
  update_time = other13.update_time;
  __isset = other13.__isset;
}
HistoryDriver& HistoryDriver::operator=(const HistoryDriver& other14) {
  drivers = other14.drivers;
  reduced = other14.reduced;
  update_time = other14.update_time;
  __isset = other14.__isset;
  return *this;
}
std::ostream& operator<<(std::ostream& out, const HistoryDriver& obj) {
  using apache::thrift::to_string;
  out << "HistoryDriver(";
  out << "drivers=" << to_string(obj.drivers);
  out << ", " << "reduced=" << to_string(obj.reduced);
  out << ", " << "update_time=" << to_string(obj.update_time);
  out << ")";
  return out;
}


PoolOrder::~PoolOrder() throw() {
}


void PoolOrder::__set_id(const std::string& val) {
  this->id = val;
}

void PoolOrder::__set_cartype(const int32_t val) {
  this->cartype = val;
}

void PoolOrder::__set_order_list(const std::vector<Order> & val) {
  this->order_list = val;
}

void PoolOrder::__set_pushtime(const int64_t val) {
  this->pushtime = val;
}

void PoolOrder::__set_drivers(const std::vector<Driver> & val) {
  this->drivers = val;
}

void PoolOrder::__set_subsidy(const double val) {
  this->subsidy = val;
}

void PoolOrder::__set_sstype(const int32_t val) {
  this->sstype = val;
}

void PoolOrder::__set_number(const int32_t val) {
  this->number = val;
}

const char* PoolOrder::ascii_fingerprint = "F7EEE70CFF3D3DDD7AC01476ABEC0F05";
const uint8_t PoolOrder::binary_fingerprint[16] = {0xF7,0xEE,0xE7,0x0C,0xFF,0x3D,0x3D,0xDD,0x7A,0xC0,0x14,0x76,0xAB,0xEC,0x0F,0x05};

uint32_t PoolOrder::read(::apache::thrift::protocol::TProtocol* iprot) {

  uint32_t xfer = 0;
  std::string fname;
  ::apache::thrift::protocol::TType ftype;
  int16_t fid;

  xfer += iprot->readStructBegin(fname);

  using ::apache::thrift::protocol::TProtocolException;


  while (true)
  {
    xfer += iprot->readFieldBegin(fname, ftype, fid);
    if (ftype == ::apache::thrift::protocol::T_STOP) {
      break;
    }
    switch (fid)
    {
      case 1:
        if (ftype == ::apache::thrift::protocol::T_STRING) {
          xfer += iprot->readString(this->id);
          this->__isset.id = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 2:
        if (ftype == ::apache::thrift::protocol::T_I32) {
          xfer += iprot->readI32(this->cartype);
          this->__isset.cartype = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 3:
        if (ftype == ::apache::thrift::protocol::T_LIST) {
          {
            this->order_list.clear();
            uint32_t _size15;
            ::apache::thrift::protocol::TType _etype18;
            xfer += iprot->readListBegin(_etype18, _size15);
            this->order_list.resize(_size15);
            uint32_t _i19;
            for (_i19 = 0; _i19 < _size15; ++_i19)
            {
              xfer += this->order_list[_i19].read(iprot);
            }
            xfer += iprot->readListEnd();
          }
          this->__isset.order_list = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 4:
        if (ftype == ::apache::thrift::protocol::T_I64) {
          xfer += iprot->readI64(this->pushtime);
          this->__isset.pushtime = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 5:
        if (ftype == ::apache::thrift::protocol::T_LIST) {
          {
            this->drivers.clear();
            uint32_t _size20;
            ::apache::thrift::protocol::TType _etype23;
            xfer += iprot->readListBegin(_etype23, _size20);
            this->drivers.resize(_size20);
            uint32_t _i24;
            for (_i24 = 0; _i24 < _size20; ++_i24)
            {
              xfer += this->drivers[_i24].read(iprot);
            }
            xfer += iprot->readListEnd();
          }
          this->__isset.drivers = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 6:
        if (ftype == ::apache::thrift::protocol::T_DOUBLE) {
          xfer += iprot->readDouble(this->subsidy);
          this->__isset.subsidy = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 7:
        if (ftype == ::apache::thrift::protocol::T_I32) {
          xfer += iprot->readI32(this->sstype);
          this->__isset.sstype = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 8:
        if (ftype == ::apache::thrift::protocol::T_I32) {
          xfer += iprot->readI32(this->number);
          this->__isset.number = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      default:
        xfer += iprot->skip(ftype);
        break;
    }
    xfer += iprot->readFieldEnd();
  }

  xfer += iprot->readStructEnd();

  return xfer;
}

uint32_t PoolOrder::write(::apache::thrift::protocol::TProtocol* oprot) const {
  uint32_t xfer = 0;
  oprot->incrementRecursionDepth();
  xfer += oprot->writeStructBegin("PoolOrder");

  xfer += oprot->writeFieldBegin("id", ::apache::thrift::protocol::T_STRING, 1);
  xfer += oprot->writeString(this->id);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("cartype", ::apache::thrift::protocol::T_I32, 2);
  xfer += oprot->writeI32(this->cartype);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("order_list", ::apache::thrift::protocol::T_LIST, 3);
  {
    xfer += oprot->writeListBegin(::apache::thrift::protocol::T_STRUCT, static_cast<uint32_t>(this->order_list.size()));
    std::vector<Order> ::const_iterator _iter25;
    for (_iter25 = this->order_list.begin(); _iter25 != this->order_list.end(); ++_iter25)
    {
      xfer += (*_iter25).write(oprot);
    }
    xfer += oprot->writeListEnd();
  }
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("pushtime", ::apache::thrift::protocol::T_I64, 4);
  xfer += oprot->writeI64(this->pushtime);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("drivers", ::apache::thrift::protocol::T_LIST, 5);
  {
    xfer += oprot->writeListBegin(::apache::thrift::protocol::T_STRUCT, static_cast<uint32_t>(this->drivers.size()));
    std::vector<Driver> ::const_iterator _iter26;
    for (_iter26 = this->drivers.begin(); _iter26 != this->drivers.end(); ++_iter26)
    {
      xfer += (*_iter26).write(oprot);
    }
    xfer += oprot->writeListEnd();
  }
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("subsidy", ::apache::thrift::protocol::T_DOUBLE, 6);
  xfer += oprot->writeDouble(this->subsidy);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("sstype", ::apache::thrift::protocol::T_I32, 7);
  xfer += oprot->writeI32(this->sstype);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("number", ::apache::thrift::protocol::T_I32, 8);
  xfer += oprot->writeI32(this->number);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldStop();
  xfer += oprot->writeStructEnd();
  oprot->decrementRecursionDepth();
  return xfer;
}

void swap(PoolOrder &a, PoolOrder &b) {
  using ::std::swap;
  swap(a.id, b.id);
  swap(a.cartype, b.cartype);
  swap(a.order_list, b.order_list);
  swap(a.pushtime, b.pushtime);
  swap(a.drivers, b.drivers);
  swap(a.subsidy, b.subsidy);
  swap(a.sstype, b.sstype);
  swap(a.number, b.number);
  swap(a.__isset, b.__isset);
}

PoolOrder::PoolOrder(const PoolOrder& other27) {
  id = other27.id;
  cartype = other27.cartype;
  order_list = other27.order_list;
  pushtime = other27.pushtime;
  drivers = other27.drivers;
  subsidy = other27.subsidy;
  sstype = other27.sstype;
  number = other27.number;
  __isset = other27.__isset;
}
PoolOrder& PoolOrder::operator=(const PoolOrder& other28) {
  id = other28.id;
  cartype = other28.cartype;
  order_list = other28.order_list;
  pushtime = other28.pushtime;
  drivers = other28.drivers;
  subsidy = other28.subsidy;
  sstype = other28.sstype;
  number = other28.number;
  __isset = other28.__isset;
  return *this;
}
std::ostream& operator<<(std::ostream& out, const PoolOrder& obj) {
  using apache::thrift::to_string;
  out << "PoolOrder(";
  out << "id=" << to_string(obj.id);
  out << ", " << "cartype=" << to_string(obj.cartype);
  out << ", " << "order_list=" << to_string(obj.order_list);
  out << ", " << "pushtime=" << to_string(obj.pushtime);
  out << ", " << "drivers=" << to_string(obj.drivers);
  out << ", " << "subsidy=" << to_string(obj.subsidy);
  out << ", " << "sstype=" << to_string(obj.sstype);
  out << ", " << "number=" << to_string(obj.number);
  out << ")";
  return out;
}


Message::~Message() throw() {
}


void Message::__set_template_type(const int32_t val) {
  this->template_type = val;
}

void Message::__set_push_type(const int32_t val) {
  this->push_type = val;
}

void Message::__set_app_type(const int32_t val) {
  this->app_type = val;
}

void Message::__set_title(const std::string& val) {
  this->title = val;
}

void Message::__set_content(const std::string& val) {
  this->content = val;
}

void Message::__set_text(const std::string& val) {
  this->text = val;
}

void Message::__set_url(const std::string& val) {
  this->url = val;
}

void Message::__set_target(const std::vector<std::string> & val) {
  this->target = val;
}

const char* Message::ascii_fingerprint = "DE77150680E85FCEF44D37C23EABCA98";
const uint8_t Message::binary_fingerprint[16] = {0xDE,0x77,0x15,0x06,0x80,0xE8,0x5F,0xCE,0xF4,0x4D,0x37,0xC2,0x3E,0xAB,0xCA,0x98};

uint32_t Message::read(::apache::thrift::protocol::TProtocol* iprot) {

  uint32_t xfer = 0;
  std::string fname;
  ::apache::thrift::protocol::TType ftype;
  int16_t fid;

  xfer += iprot->readStructBegin(fname);

  using ::apache::thrift::protocol::TProtocolException;


  while (true)
  {
    xfer += iprot->readFieldBegin(fname, ftype, fid);
    if (ftype == ::apache::thrift::protocol::T_STOP) {
      break;
    }
    switch (fid)
    {
      case 1:
        if (ftype == ::apache::thrift::protocol::T_I32) {
          xfer += iprot->readI32(this->template_type);
          this->__isset.template_type = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 2:
        if (ftype == ::apache::thrift::protocol::T_I32) {
          xfer += iprot->readI32(this->push_type);
          this->__isset.push_type = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 3:
        if (ftype == ::apache::thrift::protocol::T_I32) {
          xfer += iprot->readI32(this->app_type);
          this->__isset.app_type = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 4:
        if (ftype == ::apache::thrift::protocol::T_STRING) {
          xfer += iprot->readString(this->title);
          this->__isset.title = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 5:
        if (ftype == ::apache::thrift::protocol::T_STRING) {
          xfer += iprot->readString(this->content);
          this->__isset.content = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 6:
        if (ftype == ::apache::thrift::protocol::T_STRING) {
          xfer += iprot->readString(this->text);
          this->__isset.text = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 7:
        if (ftype == ::apache::thrift::protocol::T_STRING) {
          xfer += iprot->readString(this->url);
          this->__isset.url = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      case 8:
        if (ftype == ::apache::thrift::protocol::T_LIST) {
          {
            this->target.clear();
            uint32_t _size29;
            ::apache::thrift::protocol::TType _etype32;
            xfer += iprot->readListBegin(_etype32, _size29);
            this->target.resize(_size29);
            uint32_t _i33;
            for (_i33 = 0; _i33 < _size29; ++_i33)
            {
              xfer += iprot->readString(this->target[_i33]);
            }
            xfer += iprot->readListEnd();
          }
          this->__isset.target = true;
        } else {
          xfer += iprot->skip(ftype);
        }
        break;
      default:
        xfer += iprot->skip(ftype);
        break;
    }
    xfer += iprot->readFieldEnd();
  }

  xfer += iprot->readStructEnd();

  return xfer;
}

uint32_t Message::write(::apache::thrift::protocol::TProtocol* oprot) const {
  uint32_t xfer = 0;
  oprot->incrementRecursionDepth();
  xfer += oprot->writeStructBegin("Message");

  xfer += oprot->writeFieldBegin("template_type", ::apache::thrift::protocol::T_I32, 1);
  xfer += oprot->writeI32(this->template_type);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("push_type", ::apache::thrift::protocol::T_I32, 2);
  xfer += oprot->writeI32(this->push_type);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("app_type", ::apache::thrift::protocol::T_I32, 3);
  xfer += oprot->writeI32(this->app_type);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("title", ::apache::thrift::protocol::T_STRING, 4);
  xfer += oprot->writeString(this->title);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("content", ::apache::thrift::protocol::T_STRING, 5);
  xfer += oprot->writeString(this->content);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("text", ::apache::thrift::protocol::T_STRING, 6);
  xfer += oprot->writeString(this->text);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("url", ::apache::thrift::protocol::T_STRING, 7);
  xfer += oprot->writeString(this->url);
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldBegin("target", ::apache::thrift::protocol::T_LIST, 8);
  {
    xfer += oprot->writeListBegin(::apache::thrift::protocol::T_STRING, static_cast<uint32_t>(this->target.size()));
    std::vector<std::string> ::const_iterator _iter34;
    for (_iter34 = this->target.begin(); _iter34 != this->target.end(); ++_iter34)
    {
      xfer += oprot->writeString((*_iter34));
    }
    xfer += oprot->writeListEnd();
  }
  xfer += oprot->writeFieldEnd();

  xfer += oprot->writeFieldStop();
  xfer += oprot->writeStructEnd();
  oprot->decrementRecursionDepth();
  return xfer;
}

void swap(Message &a, Message &b) {
  using ::std::swap;
  swap(a.template_type, b.template_type);
  swap(a.push_type, b.push_type);
  swap(a.app_type, b.app_type);
  swap(a.title, b.title);
  swap(a.content, b.content);
  swap(a.text, b.text);
  swap(a.url, b.url);
  swap(a.target, b.target);
  swap(a.__isset, b.__isset);
}

Message::Message(const Message& other35) {
  template_type = other35.template_type;
  push_type = other35.push_type;
  app_type = other35.app_type;
  title = other35.title;
  content = other35.content;
  text = other35.text;
  url = other35.url;
  target = other35.target;
  __isset = other35.__isset;
}
Message& Message::operator=(const Message& other36) {
  template_type = other36.template_type;
  push_type = other36.push_type;
  app_type = other36.app_type;
  title = other36.title;
  content = other36.content;
  text = other36.text;
  url = other36.url;
  target = other36.target;
  __isset = other36.__isset;
  return *this;
}
std::ostream& operator<<(std::ostream& out, const Message& obj) {
  using apache::thrift::to_string;
  out << "Message(";
  out << "template_type=" << to_string(obj.template_type);
  out << ", " << "push_type=" << to_string(obj.push_type);
  out << ", " << "app_type=" << to_string(obj.app_type);
  out << ", " << "title=" << to_string(obj.title);
  out << ", " << "content=" << to_string(obj.content);
  out << ", " << "text=" << to_string(obj.text);
  out << ", " << "url=" << to_string(obj.url);
  out << ", " << "target=" << to_string(obj.target);
  out << ")";
  return out;
}

} // namespace
