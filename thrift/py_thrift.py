#coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('gen-py')
from scheduler.ttypes import *
from thrift.TSerialization import *

import redis

def test():
  r = redis.StrictRedis(host='localhost',port=6379)
    
  path = Path()
  path.fromcity = '北京'
  path.fromplace ='中关村'
  path.tocity = '华盛顿'
  path.toplace = '白宫'

  order = Order()
  order.id = "xd79fde6a7e711e488bf60e4001bc96"
  order.path = path
  order.phone = '18910068561'
  order.number = 2
  order.cartype = 1

  thrift_obj = serialize(order)
  r.hset('h_order', order.id, thrift_obj)
  r.lpush('l_order', order.id)

  return 
  #codestr = r.hget('h_order', "order_id")
  codestr = r.hget('h_order', "ef288158a7f811e4be5060e4001bc96")
  print len(codestr), codestr
  
  neworder = Order()
  neworder = deserialize(neworder, codestr)

  print neworder.id
  print neworder.number
  print neworder.phone


def main():
  r = redis.StrictRedis(host='localhost',port=6379)
  path = 'z_driver_北京-华盛顿'
  phone = '15810750037'
  r.zadd(path, 1, phone)

if __name__ == '__main__':
  test()

