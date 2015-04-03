#coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import redis
import time
from thrift.TSerialization import *
from ttypes import Path, Order, PoolOrder, Message

r = redis.StrictRedis(host='localhost', port=6379)

# serialize to thrift obj and send to redis
path = Path()
path.from_city = '北京'.encode('utf-8')
path.from_place = '中关村'.encode('utf-8')
path.to_city = '廊坊'.encode('utf-8')
path.to_place = '廊坊站'.encode('utf-8')

order = Order()
order.id = 123124
order.path = path
order.phone = '18910068561'
order.number = 2
order.cartype = 1
order.price = 300
order.time = int(time.time())

poolorder = PoolOrder()
poolorder.id = 'hofhsaohfoshfoehofhs'
poolorder.cartype = 1
poolorder.order_list = [order]
poolorder.pushtime = int(time.time())
poolorder.drivers = ['18910068569']
poolorder.subsidy = 13.0
poolorder.sstype = 1
poolorder.number = 2

po_obj = serialize(poolorder)

msg = Message()
msg.template_type = 0
msg.push_type = 1
msg.app_type = 1
msg.title = 'pool_order'
msg.text = 'pool order text'
msg.url = ''
msg.content = po_obj
msg.target = ['18603017596']  
msg_obj = serialize(msg)

rkey = 'l_message'
r.lpush(rkey, msg_obj)

