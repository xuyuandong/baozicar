# coding=utf-8

import time
import redis
from tornado.options import define, options


def TryLock(r, id):
  n = r.hincrby(options.lock_rm, id, 1)
  while n != 1:
    r.hincrby(options.lock_rm, id, -1)
    time.sleep(0.001)    
    n = r.hincrby(options.lock_rm, id, 1)
  return (n == 1)

def UnLock(r, id):
  return r.hincrby(options.lock_rm, id, -1)

#################

def UpdateStatus(r, order_id):
  return r.hdel(options.order_rm, order_id)

def CancelOrder(r, order_id):
  TryLock(r, order_id)
  ret = UpdateStatus(r, order_id) # delete
  UnLock(r, order_id)
  return ret

###################

def CheckStatus(r, order_list):
  for id in order_list:
    if not r.hexists(options.order_rm, id):
      return False
  return True


def ConfirmOrder(r, order_list):
  for id in order_list:
    TryLock(r, id)

  ret = CheckStatus(r, order_list)
  if ret:
    for id in order_list:
      UpdateStatus(r, id) # delete
    
  for id in order_list:
    UnLock(r, id)
  
  return ret


import datetime
if __name__ == '__main__':
  rc = redis.StrictRedis(host='127.0.0.1',port=6379)
  #rc.delete(options.order_rm)
  #rc.hset(options.order_rm, "a", "aaa")
  #rc.hset(options.order_rm, "b", "bbb")
  #rc.hset(options.order_rm, "c", "ccc")
  
  order_list = ["a", "b", "c"]
  print datetime.datetime.now()
  t = ConfirmOrder(rc, order_list)
  print datetime.datetime.now()
  print "confirm", t
