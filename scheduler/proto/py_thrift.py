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

def test(phone, person):
  r = redis.StrictRedis(host='localhost',port=6379)
    
  path = Path()
  path.from_city = 'shenzhen'
  path.from_place ='tengxundasha'
  path.to_city = 'guangzhou'
  path.to_place = 'guangzhouzhan'

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

  return
  codestr = r.hget('h_order', "ef288158a7f811e4be5060e4001bc96")
  print len(codestr), codestr
  neworder = Order()
  neworder = deserialize(neworder, codestr)
  print neworder.id
  print neworder.number
  print neworder.phone


if __name__ == '__main__':
  test('18910060009', 3)
  test('18910060001', 2)
  test('18910060002', 3)
  test('18910060003', 1)
  test('18910060004', 1)
  test('12341240007', 3)
  test('12341240008', 2)
  test('12341240006', 1)
  test('12341240005', 2)
