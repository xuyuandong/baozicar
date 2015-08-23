#coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('gen-py')
from scheduler.ttypes import *
from thrift.TSerialization import *

import redis
import time, datetime, random

def uuid(phone):
  t = datetime.datetime.now()
  y = t.year%10
  d = t.day + 31*t.month
  s = t.hour*3600 + t.minute*60 + t.second
  r = phone[-4:]
  ret = '%s%03s%05s%06s%04s'%(y,d,s, t.microsecond, r)
  return int(ret.replace(' ', '0'))

def test(phone, person, lat, lng):
  r = redis.StrictRedis(host='localhost',port=6379)
    
  path = Path()
  path.to_city = '廊坊'
  path.from_place ='傻逼酒吧'
  path.from_city = '北京'
  path.to_place = '傻逼KTV'
  path.from_lat = lat
  path.from_lng = lng 
  path.to_lat = 116
  path.to_lng = 40

  order = Order()
  order.id = uuid(phone)
  order.path = path
  order.phone = phone
  order.number = person
  order.cartype = 0
  order.price = 10
  order.time = int(time.time()) 

  thrift_obj = serialize(order)
  r.hset('h_order', order.id, thrift_obj)
  r.lpush('l_order', order.id)



if __name__ == '__main__':
  test('18810308350', 2, 39.863697, 116.428565)
  #test('18810308350', 2, 39.871575, 116.465751)
