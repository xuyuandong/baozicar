# coding=utf-8

import time
import redis

LOCK_TABLE = "lock"
ORDER_TABLE = "order"

def TryLock(r, id):
  n = r.hincrby(LOCK_TABLE, id, 1)
  while n != 1:
    r.hincrby(LOCK_TABLE, id, -1)
    print "sleep 0.001"
    time.sleep(0.001)    
    n = r.hincrby(LOCK_TABLE, id, 1)
  return (n == 1)

def UnLock(r, id):
  return r.hincrby(LOCK_TABLE, id, -1)

#################

def UpdateStatus(r, order_id):
  return r.hdel(ORDER_TABLE, order_id)

def CancelOrder(r, order_id):
  TryLock(r, order_id)
  ret = UpdateStatus(r, order_id) # delete
  time.sleep(0.002)
  UnLock(r, order_id)
  return ret

###################

def CheckStatus(r, order_list):
  for id in order_list:
    if not r.hexists(ORDER_TABLE, id):
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


import sys
import datetime
if __name__ == '__main__':
  rc = redis.StrictRedis(host='127.0.0.1',port=6379)
  #rc.hset(ORDER_TABLE, "a", "aaa")
  #rc.hset(ORDER_TABLE, "b", "bbb")
  #rc.hset(ORDER_TABLE, "c", "ccc")
  
  #order_list = ["a", "b", "c"]
  #ConfirmOrder(rc, order_list)
  print datetime.datetime.now()
  t = CancelOrder(rc, sys.argv[1])
  print datetime.datetime.now()
  print "cancel ", sys.argv[1], t
