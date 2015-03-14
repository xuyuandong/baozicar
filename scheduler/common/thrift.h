#ifndef _THRIFT_H_
#define _THRIFT_H_

#include <string>
#include <boost/shared_ptr.hpp>
#include <boost/scoped_ptr.hpp>
#include <thrift/protocol/TBinaryProtocol.h>
#include <thrift/transport/TTransportUtils.h>
#include "base/logging.h"

using namespace ::apache::thrift;
using namespace ::apache::thrift::protocol;
using namespace ::apache::thrift::transport;

namespace base {

template <typename T>
bool StringToThrift(const std::string &buffer, T *object) {
  T tmp;
  if (StringToThriftFast(buffer, &tmp)) {
    *object = tmp;
    return true;
  }
  return false;
}

template <typename T>
inline bool StringToThriftFast(const std::string &buffer, T *object) {
  boost::shared_ptr<TMemoryBuffer> membuffer(new TMemoryBuffer(
        const_cast<uint8_t*>(reinterpret_cast<const uint8_t*>(buffer.c_str())),
        buffer.size()));
  boost::scoped_ptr<TProtocol> protocol(new TBinaryProtocol(membuffer));
  try {
    object->read(protocol.get());
  } catch (const TException &ex) {
    LOG(ERROR) << "StringToThrift failed: " << ex.what();
    return false;
  }
  return true;
}

template <typename T>
const std::string ThriftToString(const T *object) {
  boost::shared_ptr<TMemoryBuffer> membuffer(new TMemoryBuffer());
  boost::scoped_ptr<TProtocol> protocol(new TBinaryProtocol(membuffer));
  object->write(protocol.get());
  uint8_t* buffer = NULL;
  uint32_t size = 0;
  membuffer->getBuffer(&buffer, &size);
  return std::string(reinterpret_cast<const char*>(buffer), size);
}

class ThriftTool {
  public:
    ThriftTool()
      :membuffer_(new TMemoryBuffer()),
      protocol_(new TBinaryProtocol(membuffer_)) {
    }
    ~ThriftTool() {}

    template <typename T>
    bool StringToThrift(const std::string& buffer, T* object) {
      T tmp;
      membuffer_->resetBuffer(
          const_cast<uint8_t*>(reinterpret_cast<const uint8_t*>(buffer.c_str())),
          buffer.size());
      try {
        tmp.read(protocol_.get());
      } catch (const TException &ex) {
        LOG(ERROR) << "StringToThrift failed: " << ex.what();
        return false;
      }
      *object = tmp;
      return true;
    }

    // not safe
    template <typename T>
    bool ThriftToString(const T* object, std::string* buffer) {
      membuffer_ -> resetBuffer();
      try {
        object->write(protocol_.get());
      } catch (const TException& ex) {
        LOG(ERROR) << "ThriftToString failed: " << ex.what();
        return false;
      }
      uint8_t* buf = NULL;
      uint32_t buf_size = 0;
      membuffer_->getBuffer(&buf, &buf_size);
      buffer->assign(reinterpret_cast<const char*>(buf), buf_size);
      return true;
    }

  private:
    boost::shared_ptr<TMemoryBuffer> membuffer_;
    boost::scoped_ptr<TProtocol> protocol_;
    
  DISALLOW_COPY_AND_ASSIGN(ThriftTool);
};

}  // end namespace

#endif  // _THRIFT_H_
