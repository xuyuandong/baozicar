#coding=utf-8

import time,datetime
import tornado.web
import tornado.gen
import json
import base

from tornado.concurrent import run_on_executor
from tornado.options import define, options
from tornado.log import app_log

from futures import ThreadPoolExecutor
from thrift.TSerialization import *

import Crypto
import base64
import binascii

from Crypto import Signature
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from urllib import urlopen

################# coding comment ####################################
# status_code: 200 OK 201 Failed
# order_type: 0 carpool 1 specialcar
# order_status: 0 wait 1 confirm 2 toeval 3 done 4 cancel
# coupon_status: 0 normal 1 expired
#####################################################################
from base import TempType, PushType, AppType, OrderType, OrderStatus, OLType
from base import POType, POStatus, CouponStatus, DriverStatus
from base import BaseHandler
from ttypes import Path, Order, Message

define("alipay_partner", default='2088811966740952', help="alipay partner id")
define("alipay_url", default="https://mapi.alipay.com/gateway.do?service=notify_verify&", help="verify url")
define("alipay_public_key", default='/home/deploy/conf/alipay_public_key_pkcs8.pem', help="")

def base64ToString(s):
  try:
    return base64.decodestring(s)
  except Exception, e:
    app_log.error('base64decode:%s', e)
    return ''

# /alipay_notify
class AlipayNotifyHandler(BaseHandler):
  def post(self):
    # verify request is securety
    if not self.verify():
      self.write('failed')
      return
    
    # check trade is successful
    trade_status = self.get_argument('trade_status')
    if trade_status != 'TRADE_FINISHED' or trade != 'TRADE_SUCCESS':
      self.write('failed')
      return

    # record information
    trade_no = self.get_argument('trade_no')
    order_id = self.get_argument('out_trade_no')
    price = self.get_argument('total_fee')
      
    buyer = self.get_argument('buyer_email')
    buyerid = self.get_argument('buyer_id')
    seller = self.get_argument('seller_email')
    sellerid = self.get_argument('seller_id')
    gmtc = self.get_argument('gmt_create')
    gmtp = self.get_argument('gmt_payment')

    # insert into mysql
    table = 'cardb.t_payment'
    sql = "insert into %s \
        (pay_id, order_id, price, status, buyer, seller, \
        buyer_id, seller_id, gmt_create, gmt_pay, extra_info, dt)\
        values (%s, %s, '%s', %s, %s, '%s', '%s', '%s', '%s', '%s', '%s', '', null)"\
        %(trade_no, order_id, price, 0, buyer, seller, buyerid, sellerid, gmtc, gmtp)
    self.db.execute(sql)

    # push order to scheduler
    self.process(order_id, trade_no, price)
    # return result
    self.write('success')


  def verify(self):
    args = self.request.arguments
    return self.verify_sign(args) and self.verify_source(args)

  def verify_sign(self, args):
    params = []
    for key in sorted(args):
      if key == 'sign' or key == 'sign_type' or len(args[key]) == 0:
        continue
      params.append( '='.join([key, args[key]]) )
    
    sign = args['sign']
    pre_sign_str = '&'.join(params)
    return self.verify_rsa(pre_sign_str, sign)  

  def verify_rsa(self, pre_sign_str, sign):
    hash = SHA.new(pre_sign_str)
    signature = base64ToString(sign)
    
    key = RSA.importKey(self.alipay_public_key)
    verifier = PKCS1_v1_5.new(key)
    return verifier.verify(hash, signature)

  def verify_source(self, args):
    if 'notify_id' not in args:
      return True
    
    partner = options.alipay_partner
    notify_id = self.get_argument('notify_id')
    url = options.alipay_url + 'partner=' + partner + '&notify_id=' + notify_id  
    
    ret = urlopen(url).read()
    return (ret.lower().strip() == 'true')


  def process(self, order_id, pay_id, fact_price):
    # update order db with pay_id
    table = 'cardb.t_order'
    sql = "update %s set pay_id=%s, status=%s, fact_price=%s \
        where id=%s"%(table, pay_id, OrderStatus.wait, fact_price, order_id)
    self.db.execute(sql)

    # select info to send
    sql = "select order_type, status, phone, name, start_time,\
           from_city, from_place, to_city, to_place, num, \
           price, coupon_id, coupon_price \
           from %s where id=%s"%(table, order_id)
    obj = self.db.get(sql)

    # mark coupon is used
    if obj.coupon_price > 0:
      table = 'cardb.t_coupon'
      sql = "update %s set status=%s where id=%s"%(table, CouponStatus.used, obj.coupon_id)
      self.db.execute(sql)

    # serialize to thrift obj and send to redis
    path = Path()
    path.from_city = obj.from_city.encode('utf-8')
    path.from_place = obj.from_place.encode('utf-8')
    path.to_city = obj.to_city.encode('utf-8')
    path.to_place = obj.to_place.encode('utf-8')

    order = Order()
    order.id = order_id
    order.path = path
    order.phone = obj.phone
    order.number = int(obj.person_num)
    order.cartype = int(obj.order_type)
    order.price = int(obj.price)

    thrift_obj = serialize(order)
    pipe = self.r.pipeline()
    pipe.hset(options.order_rm, order_id, thrift_obj)
    pipe.lpush(options.order_rq, order_id)
    pipe.execute()

