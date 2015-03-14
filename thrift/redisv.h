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
      ln_ = "l_" + name;
      hn_ = "h_" + name;
      Recover();
    }

    void Recover() {
      ReplyObj t;
      t = r_->execute("DEL %s", ln_.c_str());
      t = r_->execute("HKEYS %s", hn_.c_str());
      if (t.OK() && t.Num() > 0) {
        ReplyObj ot;
        for (size_t i = 0; i < t.Num(); ++i) {
          ot = r_->execute("LPUSH %s %s", ln_.c_str(), t.Ele(i)->str);
        }
      }
    }

    void Put(const std::string& key, const std::string& val) {
      ReplyObj t;
      t = r_->execute("HSET %s %b %b", hn_.c_str(), 
          key.c_str(), key.size(), val.c_str(), val.size());
      t = r_->execute("LPUSH %s %s", ln_.c_str(), key.c_str());
    }

    redisReply* Pop() {
      ReplyObj t;
      t = r_->execute("RPOP %s", ln_.c_str());
      if (t.OK() && t.Type() == REDIS_REPLY_STRING) {
        redisReply* p = r_->execute("HGET %s %s", hn_.c_str(), t.Str());
        if (p->type == REDIS_REPLY_NIL) {
          freeReplyObject(p);
          return NULL;
        }
        return p;
      }
      return NULL;
    }

    int Check(const std::string& key){
      ReplyObj t;
      t = r_->execute("HEXISTS %s %s", hn_.c_str(), key.c_str());
      return t.Int();
    }

    int Len() {
      ReplyObj t;
      t = r_->execute("LLEN %s", ln_.c_str());
      return t.Int();
    }

    int Size() {
      ReplyObj t;
      t = r_->execute("HLEN %s", hn_.c_str());
      return t.Int();
    }

  private:
    Redispp* r_;
    std::string hn_;
    std::string ln_;

};


}  // end namespace

#endif  // _REDISPP_H_
