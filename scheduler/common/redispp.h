#ifndef _REDISPP_H_
#define _REDISPP_H_

#include <string>
#include <hiredis/hiredis.h>
#include "base/logging.h"

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
    inline std::string String() {
      std::string tmp;
      tmp.assign(r_->str, r_->len);
      return tmp;
    }

  private:
    ReplyObj(const ReplyObj&); // not allowed 
    redisReply* r_;
};

/* Not Thread-Safe Client */
class Redispp {
  public:
    Redispp(const char* host, int port) {
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
};

class RedisLock {
  public:
    static bool TryLock(Redispp* r, const std::string& var) {
      ReplyObj t;
      t = r->execute("INCR %s", var.c_str());
      if (t.Int() != 1) {
        t = r->execute("DECR %s", var.c_str());
        return false;
      }
      return true;
    }
    static void UnLock(Redispp* r, const std::string& var) {
      ReplyObj t;
      t = r->execute("DECR %s", var.c_str());
    }
};

class RedisMap {
  public:
    RedisMap() : r_(NULL) {}
    void Init(Redispp* r, const std::string& name) {
      r_ = r;
      hn_ = "h_" + name;
    }

    void Set(const std::string& key, const std::string& val) {
      ReplyObj t;
      t = r_->execute("HSET %s %b %b", hn_.c_str(), 
          key.c_str(), key.size(), val.c_str(), val.size());
    }

    redisReply* Get(const std::string& key) {
      redisReply* p = r_->execute("HGET %s %s", hn_.c_str(), key.c_str());
      if (p->type == REDIS_REPLY_NIL) {
        freeReplyObject(p);
        return NULL;
      }
      return p;
    }
    
    int Size() {
      ReplyObj t;
      t = r_->execute("HLEN %s", hn_.c_str());
      return t.Int();
    }

  private:
    Redispp* r_;
    std::string hn_;
};

class RedisStructMap {
  public:
    RedisStructMap() : r_(NULL) {}
    void Init(Redispp* r, const std::string& name) {
      r_ = r;
      hp_ = "h_" + name + "_";
    }

    redisReply* Get(const std::string& key, const std::string& structkey) {
      std::string hkey = hp_ + key;
      redisReply* p = r_->execute("HGET %b %b", hkey.c_str(), hkey.size(), 
          structkey.c_str(), structkey.size());
      if (p->type == REDIS_REPLY_NIL) {
        freeReplyObject(p);
        return NULL;
      }
      return p;
    }
    
  private:
    Redispp* r_;
    std::string hp_;
};


class RedisQueue {
  public:
    RedisQueue() :r_(NULL) {}
    void Init(Redispp* r, const std::string& name) {
      r_ = r;
      ln_ = "l_" + name;
    }
    
    void Put(const std::string& obj) {
      ReplyObj t;
      VLOG(2) << ln_;
      t = r_->execute("LPUSH %b %b", ln_.c_str(), ln_.size(), obj.c_str(), obj.size());
    }
    
    redisReply* Pop() {
      redisReply* t = r_->execute("RPOP %b", ln_.c_str(), ln_.size());
      if (t->type != REDIS_REPLY_STRING) {
        freeReplyObject(t);
        return NULL;
      }
      return t;
    }

    int Len() {
      ReplyObj t;
      t = r_->execute("LLEN %s", ln_.c_str());
      return t.Int();
    }

  private:
    Redispp* r_;
    std::string ln_;
};

class RedisMapQueue {
  public:
    RedisMapQueue() :r_(NULL) {}
    void Init(Redispp* r, const std::string& name){
      r_ = r;
      ln_ = "l_" + name;
      hn_ = "h_" + name;
    }

    void Recover() {
      ReplyObj t;
      t = r_->execute("DEL %s", ln_.c_str());
      t = r_->execute("HKEYS %s", hn_.c_str());
      if (t.OK() && t.Num() > 0) {
        for (size_t i = 0; i < t.Num(); ++i) {
          PutKey(t.Ele(i)->str);
        }
      }
    }

    int Check(const std::string& key){
      ReplyObj t;
      t = r_->execute("HEXISTS %s %b", hn_.c_str(), key.c_str(), key.size());
      return t.Int();
    }

    redisReply* Get(const std::string& key) {
      redisReply* p = r_->execute("HGET %s %b", hn_.c_str(), key.c_str(), key.size());
      if (p->type == REDIS_REPLY_NIL) {
        freeReplyObject(p);
        return NULL;
      }
      return p;
    }

    void Del(const std::string& key) {
      ReplyObj t;
      t = r_->execute("HDEL %s %b", hn_.c_str(), key.c_str(), key.size());
    }

    void PutKey(const std::string& key) {
      ReplyObj t;
      t = r_->execute("LPUSH %s %s", ln_.c_str(), key.c_str());
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
        return Get(t.Str());
      }
      return NULL;
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

class RedisPriorityQueue {
  public:
    RedisPriorityQueue() : r_(NULL) {}
    void Init(Redispp* r, const std::string& name) {
      r_ = r;
      zn_ = "z_" + name + "_";
    }

    void Put(const std::string& key, const std::string& val, int priority) {
      ReplyObj t;
      std::string zset = zn_ + key;
      t = r_->execute("ZADD %s %d %s", zset.c_str(), priority, val.c_str());
    }

    redisReply* Get(const std::string& key, int start, int stop) {
      std::string zset = zn_ + key;
      return r_->execute("ZRANGE %s %d %d", zset.c_str(), start, stop);
    }

    redisReply* GetWithScore(const std::string& key, int start, int stop) {
      std::string zset = zn_ + key;
      return r_->execute("ZRANGE %s %d %d WITHSCORES", zset.c_str(), start, stop);
    }

    int Update(const std::string& key, const std::string& val, int priority) {
      ReplyObj t;
      std::string zset = zn_ + key;
      t = r_->execute("ZINCRBY %s %d %s", zset.c_str(), priority, val.c_str());
      return t.Int();
    }

    void Del(const std::string& key, const std::string& val) {
      ReplyObj t;
      std::string zset = zn_ + key;
      t = r_->execute("ZREM %s %s", zset.c_str(), val.c_str());
    }

    int Size(const std::string& key) {
      ReplyObj t;
      std::string zset = zn_ + key;
      t = r_->execute("ZCARD %s", zset.c_str());
      return t.Int();
    }

  private:
    Redispp* r_;
    std::string zn_;
};


}  // end namespace

#endif  // _REDISPP_H_
