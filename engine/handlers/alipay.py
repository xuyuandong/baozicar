#coding=utf-8

import time,datetime
import tornado.web
import tornado.gen
import json
import base

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.concurrent import run_on_executor
from tornado.options import define, options
from tornado.log import app_log

from futures import ThreadPoolExecutor
from thrift.TSerialization import *

import md5
import Crypto
import base64
import binascii
import urllib

from Crypto import Signature
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import xml.etree.ElementTree as ET

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

define("wxpay_partner", default='1237030902', help="wxpay partner id")
define("wxpay_md5_key", default='c8gv99modak1qv8r02j97c4u67dcgoma', help="wxpay md5 key")
define("wxpay_url", default='https://gw.tenpay.com/gateway/verifynotifyid.xml?', help="verify url")

define("unionpay_md5_key", default='e82e742b60d7e202f3d85b5668d03f6d', help='unionpay md5 key')

def base64ToString(s):
  try:
    return base64.decodestring(s)
  except Exception, e:
    app_log.error('exception base64decode :%s', e)
    return ''


class PayOrderHandler(object):
  def process(self, handler, order_id, pay_id, fact_price):
    # update order db with pay_id
    table = 'cardb.t_order'
    sql = "update %s set pay_id=%s, status=%s, fact_price=%s \
        where id=%s"%(table, pay_id, OrderStatus.wait, fact_price, order_id)
    handler.db.execute(sql)

    # select info to send
    sql = "select order_type, status, phone, name, start_time,\
           from_city, from_place, to_city, to_place, num, \
           start_time, price, coupon_id, coupon_price, \
           from_lat, from_lng, to_lat, to_lng, driver \
           from %s where id=%s"%(table, order_id)
    obj = handler.db.get(sql)

    # mark coupon is used
    if obj is not None and obj.coupon_price > 0:
      table = 'cardb.t_coupon'
      sql = "update %s set status=%s where id=%s"%(table, CouponStatus.used, obj.coupon_id)
      handler.db.execute(sql)

    if obj is None:
      return

    if obj.order_type == OrderType.booking:
      self.send_booking_msg(handler, order_id, obj)
    else:
      self.send_schedule_msg(handler, order_id, obj)

  def send_booking_msg(self, handler, order_id, obj):
    if obj.driver == '-':
      return

    pushmsg = Message()
    pushmsg.template_type = TempType.notify
    pushmsg.push_type = PushType.one
    pushmsg.app_type = AppType.driver
    pushmsg.title = 'booking_deal'
    
    jdict = { 'title': 'booking_deal',
        'order_id': order_id
        }
    pushmsg.content = json.dumps(jdict)
    pushmsg.target = [obj.driver]
      
    thrift_obj = serialize(pushmsg)
    self.r.lpush(options.queue, thrift_obj)

  def send_schedule_msg(self, handler, order_id, obj):
    # serialize to thrift obj and send to redis
    path = Path()
    path.from_city = obj.from_city.encode('utf-8')
    path.from_place = obj.from_place.encode('utf-8')
    path.to_city = obj.to_city.encode('utf-8')
    path.to_place = obj.to_place.encode('utf-8')

    path.from_lat = obj.from_lat
    path.from_lng = obj.from_lng
    path.to_lat = obj.to_lat
    path.to_lng = obj.to_lng

    order = Order()
    order.id = int(order_id)
    order.path = path
    order.phone = obj.phone
    order.number = int(obj.num)
    order.cartype = int(obj.order_type)
    order.price = int(obj.price)
    order.time = int(time.time())
    order.start_time = obj.start_time

    thrift_obj = serialize(order)
    
    pipe = handler.r.pipeline()
    pipe.hset(options.order_rm, order_id, thrift_obj)
    pipe.lpush(options.order_rq, order_id)
    pipe.execute()



# /alipay_notify
class AlipayNotifyHandler(BaseHandler):
  @tornado.web.asynchronous
  @tornado.gen.coroutine
  def post(self):
    try:
      # check trade is successful
      trade_status = self.get_argument('trade_status')
      if trade_status != 'TRADE_FINISHED' and trade_status != 'TRADE_SUCCESS':
        app_log.info('trade status: %s', trade_status)
        self.write('failed')
        return
    
      args = self.request.arguments
      # verify request is securety
      if not self.verify_sign(args):
        app_log.info('failed to check signature')
        self.write('failed')
        return
      # verify notify coming source
      source = yield self.verify_source()
      if source.body.lower().strip() != 'true':
        app_log.info('failed to check notify_id')
        self.write('failed')
        return
    except Exception, e:
      app_log.info('exception:%s', e)
      self.write('failed')
      return

    self.paylog.info(self.request.arguments)
    
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

    # check and make sure not redo 
    table = 'cardb.t_payment'
    sql = "select id from %s where trade_no='%s' limit 1"%(table, trade_no)
    obj = self.db.get(sql)
    if obj is not None:
      self.write('success')
      return
      
    # insert into mysql
    pay_id = base.uuid(order_id)

    table = 'cardb.t_payment'
    sql = "insert into %s \
        (id, trade_no, order_id, price, status, buyer, seller, \
        buyer_id, seller_id, gmt_create, gmt_payment, extra_info, dt)\
        values (%s, %s, '%s', %s, %s, '%s', '%s', '%s', '%s', '%s', '%s', '', null)"\
        %(table, pay_id, trade_no, order_id, price, 0, \
        buyer, seller, buyerid, sellerid, gmtc, gmtp)
    self.db.execute(sql)
    
    # push order to scheduler
    handler = PayOrderHandler()
    handler.process(self, order_id, pay_id, price)

    # return result
    self.write('success')


  def verify_sign(self, args):
    params = []
    for key in sorted(args):
      if key == 'sign' or key == 'sign_type' or len(args[key]) == 0:
        continue
      params.append( '='.join([key, args[key][0]]) )
    
    sign = args['sign'][0]
    pre_sign_str = '&'.join(params)
    return self.verify_rsa(pre_sign_str, sign)  

  def verify_rsa(self, pre_sign_str, sign):
    hash = SHA.new(pre_sign_str)
    signature = base64ToString(sign)
    
    key = RSA.importKey(self.alipay_public_key)
    verifier = PKCS1_v1_5.new(key)
    return verifier.verify(hash, signature)

  def verify_source(self):
    partner = options.alipay_partner
    notify_id = self.get_argument('notify_id')
    url = options.alipay_url + 'partner=' + partner + '&notify_id=' + notify_id  
    
    client = AsyncHTTPClient()
    return client.fetch(url)



# /wxpay_notify
class WxpayNotifyHandler(BaseHandler):
  @tornado.web.asynchronous
  @tornado.gen.coroutine
  def post(self):
    args = self.parse(self.request.body)

    return_code = args['return_code']
    result_code = args['result_code']
    app_log.info('return=%s result=%s', return_code, result_code)
    
    if return_code != 'SUCCESS' or result_code != 'SUCCESS':
      self.write('<xml><return_code><![CDATA[FAIL]]></return_code></xml>')
      return

    self.update_payment(args)

  def parse(self, xml_str):
    root = ET.fromstring(xml_str)
    args = {}
    for child in root:
      args[child.tag] = child.text
    return args

  def update_payment(self, args):
    trade_no = args['transaction_id']
    order_id = args['out_trade_no']
    price = float(args['total_fee'])/100.0 #wxpay unit is fen
    app_log.info('wxpay order_id = %s', order_id)

    buyer = args['openid']
    buyerid = args['openid']
    seller = args['appid']
    sellerid = args['mch_id']

    time_end = args['time_end']
    t_struct = datetime.datetime.strptime(time_end, "%Y%m%d%H%M%S")
    t_str = t_struct.strftime('%Y-%m-%d %H:%M:%S')
    gmtc = t_str
    gmtp = t_str
    
    extra_info = 'is_subscribe:%s'%(args['is_subscribe'])

    # check and make sure not redo 
    table = 'cardb.t_payment'
    sql = "select id from %s where trade_no='%s' limit 1"%(table, trade_no)
    obj = self.db.get(sql)
    if obj is not None:
      self.write('<xml><return_code><![CDATA[SUCCESS]]></return_code></xml>')
      return

    # insert into mysql
    pay_id = base.uuid(order_id)
    sql = "insert into %s \
        (id, trade_no, order_id, price, status, buyer, seller, \
        buyer_id, seller_id, gmt_create, gmt_payment, extra_info, dt)\
        values (%s, %s, '%s', %s, %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', null)"\
        %(table, pay_id, trade_no, order_id, price, 1, \
        buyer, seller, buyerid, sellerid, gmtc, gmtp, extra_info)
    self.db.execute(sql)

    # push order to scheduler
    handler = PayOrderHandler()
    handler.process(self, order_id, pay_id, price)
    
    self.write('<xml><return_code><![CDATA[SUCCESS]]></return_code></xml>')
    

# /unionpay_notify2
class UnionpayNotifyHandler(BaseHandler):
  @tornado.web.asynchronous
  @tornado.gen.coroutine
  def post(self):
    # check signature
    if not self.check_sign():
      return

    # check md5
    if not self.check_md5():
      return

    # success
    sellerid = self.get_argument('merId')
    trade_no = self.get_argument('queryId')
    order_id = self.get_argument('orderId')

    txn_price = self.get_argument('txnAmt')
    txn_time = self.get_argument('txnTime')
    
    t_struct = datetime.datetime.strptime(txn_time, "%Y%m%d%H%M%S")
    gmt_time = t_struct.strftime('%Y-%m-%d %H:%M:%S')
    price = float(txn_price) / 100.0

    # check and make sure not redo 
    table = 'cardb.t_payment'
    sql = "select id from %s where trade_no='%s' limit 1"%(table, trade_no)
    obj = self.db.get(sql)
    if obj is not None:
      app_log.info('already receive this callback before')
      self.write('failed')
      return

    app_log.info('unionpay order_id=%s', order_id)

    # get buyer info
    table = 'cardb.t_order'
    sql = "select name, phone from %s where id=%s"%(table, order_id)
    obj = self.db.get(sql)
    buyer = '-'
    buyerid = '-'
    if obj is not None:
      buyer = obj.name
      buyerid = obj.phone

    # insert into mysql
    pay_id = base.uuid(order_id)
    table = 'cardb.t_payment'
    sql = "insert into %s \
        (id, trade_no, order_id, price, status, buyer, seller, \
        buyer_id, seller_id, gmt_create, gmt_payment, extra_info, dt)\
        values (%s, %s, '%s', %s, %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', null)"\
        %(table, pay_id, trade_no, order_id, price, 2, \
        buyer, '-', buyerid, sellerid, gmt_time, gmt_time, '-')
    self.db.execute(sql)

    # push order to scheduler
    handler = PayOrderHandler()
    handler.process(self, order_id, pay_id, price)
    
    self.write('success')
  
  def check_sign(self):
    return_code = self.get_argument('respCode')
    return_msg = self.get_argument('respMsg')
    check_sign = self.get_argument('checksignsucc')

    if check_sign == '0': # failed
      app_log.info('unionpay code=%s msg=%s check=%s', return_code, return_msg, check_sign)
      self.write('failed')
      return False

    return True

  def check_md5(self):
    sign = self.get_argument('signature')
    order_id = self.get_argument('orderId')
    check_sign = self.get_argument('checksignsucc')

    v = md5.md5(options.unionpay_md5_key + urllib.unquote(sign) + order_id + check_sign)
    
    mds = self.get_argument('checksum')
    if mds != v.hexdigest():
      app_log.info('unionpay md5 check failed')
      self.write('failed')
      return False
    
    return True


