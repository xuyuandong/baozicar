#ifndef _REDISPP_H_
#define _REDISPP_H_

#include <hiredis.h>
#include <iostream>
namespace base {

class ReplyObj {
  public:
    ReplyObj(redisReply* r = NULL)
      : r_(r) {}
    ~ReplyObj() {
      if (r_ != NULL)
        freeReplyObject(r_);
    }
    void operator=(redisReply* r) {
      if (r_ != r) {
        if (r_ != NULL) 
          freeReplyObject(r_);
        r_ = r;
      }
    }
    inline bool OK() {
      return (r_ != NULL);
    }
    inline int Type() {
      return r_->type;
    }
    inline long long Int() {
      return r_->integer;
    }
    inline const char* Str() {
      return r_->str;
    }
    inline int Len() {
      return r_->len;
    }
    inline size_t Num() {
      return r_->elements;
    }
    inline redisReply* Ele(int idx) const {
      return r_->element[idx];
    }

  private:
    ReplyObj(const ReplyObj&); // not allowed 
    redisReply* r_;
};

/* Not Thread-Safe Client */
class Redispp {
  public:
    Redispp(const char* host, int port) 
      :host_(host), port_(port) {
        redis_ = redisConnect(host, port);
      }
    ~Redispp() {
      redisFree(redis_);
    }

    redisReply* execute(const char *format, ...) {
      void *reply = NULL;
      va_list ap;
      va_start(ap,format);
      reply = redisvCommand(redis_, format, ap);
      va_end(ap);
      return (redisReply*)reply;
    }

  private:
    redisContext* redis_; 
    const char* host_;
    int port_;
};

class RedisQueue {
  public:
    RedisQueue(Redispp* r, const std::string& name) : r_(r){
      zn_ = "z_" + name;
      hn_ = "h_" + name;
      cn_ = "c_" + name;
      r_ -> execute("SET %s 0", cn_.c_str());
    }

    redisReply* Put(const std::string& key, const std::string& val) {
      std::cout << "r put" << std::endl;
      ReplyObj t;
      t = r_->execute("INCR %s", cn_.c_str());
      std::cout << "r " << t.Int() << std::endl;
      r_->execute("SET %b %b", key.c_str(), key.size(), val.c_str(), val.size());
      std::cout << "r .." << std::endl;
      return r_->execute("ZADD %s %d %s", zn_.c_str(), t.Int(), key.c_str());
    }

    redisReply* Pop(int idx) {
      ReplyObj t;
      std::cout << "r pop" <<std::endl;
      t = r_->execute("ZRANGEBYSCORE %s %d %d", zn_.c_str(), idx, idx);
      std::cout << "r --" << std::endl;
      if (t.Type() == REDIS_REPLY_ARRAY && t.Num() == 1) {
        const char* key = t.Ele(0)->str;
        return r_->execute("GET %s", key);
      } 
      return NULL;
    }

    int Size() {
      ReplyObj t;
      t = r_->execute("ZCARD %s", zn_.c_str());
      return t.Int();
    }

  private:
    Redispp* r_;

    std::string zn_;
    std::string hn_;
    std::string cn_;

};


}  // end namespace

#endif  // _REDISPP_H_
