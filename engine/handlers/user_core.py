#coding=utf-8

import time,datetime
import tornado.web
import tornado.gen
import json
import base
import order_util

from tornado.concurrent import run_on_executor
from tornado.options import define, options
from tornado.log import app_log

from futures import ThreadPoolExecutor
from thrift.TSerialization import *

try:
  from xml.etree import cElementTree as ET
except ImportError:
  from xml.etree import ElementTree as ET

################# coding comment ####################################
# status_code: 200 OK 201 Failed
# order_type: 0 carpool 1 specialcar
# order_status: 0 wait 1 confirm 2 toeval 3 done 4 cancel
# order_list_type: 0 booked 1 toeval 2 done 3 all
# coupon_status: 0 normal 1 expired
#####################################################################
from base import LoginType, TempType, PushType, AppType, OrderType, OrderStatus, OLType
from base import POType, POStatus, CouponStatus, DriverStatus
from base import BaseHandler
from ttypes import Path, Order, Message


# /select_coupon
class SelectCouponHandler(BaseHandler):
  @base.authenticated
  #def get(self):
  def post(self):
    order_id = self.get_argument('order_id')
    coupon_id = self.get_argument('coupon_id')
    coupon_price = self.get_argument('coupon_price')

    table = 'cardb.t_coupon'
    sql = "select status from %s where id=%s limit 1"%(table, coupon_id)
    obj = self.db.get(sql)

    if obj is None or obj.status != CouponStatus.normal:
      self.write({'status_code':201, 'error_msg':'The coupon is invalid'})
      return

    sql = "update %s set status=%s where id=%s"%(table, CouponStatus.locked, coupon_id)
    self.db.execute(sql)

    table = 'cardb.t_order'
    sql = "update %s set coupon_id=%s, coupon_price=%s \
        where id=%s"%(table, coupon_id, coupon_price, order_id)
    self.db.execute(sql)

    self.write({'status_code':200, 'error_msg':''})

# /submit_order
class SubmitOrderHandler(BaseHandler):
  @base.authenticated
  def post(self):
    phone = self.current_user
    # check conflict
    if self.check_conflict(phone):
      return

    order_type = self.get_argument("order_type")

    from_city = self.get_argument("from_city")
    from_place = self.get_argument("from_place")
    to_city = self.get_argument("to_city")
    to_place = self.get_argument("to_place")

    name = self.get_argument("name")
    person_num = self.get_argument("person_num")
    price = self.get_argument("total_price")

    from_lat = self.get_argument('from_lat')
    from_lng = self.get_argument('from_lng')
    to_lat = self.get_argument('to_lat')
    to_lng = self.get_argument('to_lng')

    pay_id = 0 #self.get_argument('pay_id')
    fact_price = 0 #self.get_argument("fact_price")
    coupon_id = 0 #self.get_argument("coupon_id")
    coupon_price = 0 #self.get_argument("coupon_price")

    # special car argument
    extra_msg = ''
    start_time = ''
    if int(order_type) >= OrderType.special:
      extra_msg = self.get_argument('extra_msg')
      start_time = self.get_argument('start_time')

    app_log.info('submit user phone=%s, name=%s', phone, name)

    # insert into mysql db
    order_id = base.uuid(phone)
    table = 'cardb.t_order'
    sql = "insert into %s (id, order_type, status, phone, name, start_time,\
           from_city, from_place, to_city, to_place, num, msg,\
           pay_id, price, fact_price, coupon_id, coupon_price, \
           from_lat, from_lng, to_lat, to_lng, dt) \
           values(%s, %s, %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s',\
           %s, '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, null)"\
           %(table, order_id, order_type, OrderStatus.notpay, phone, name, start_time,
               from_city, from_place, to_city, to_place, person_num, extra_msg,
               pay_id, price, fact_price, coupon_id, coupon_price,
               from_lat, from_lng, to_lat, to_lng)
    self.db.execute(sql)

    # process booking order
    if order_type == OrderType.booking:
      self.process_booking_order(phone, order_id)

    # return result
    msg = {'status_code':200,
           'error_msg':'',
           'order_id':order_id
           }
    self.write(msg)

  def check_conflict(self, phone):
    table = 'cardb.t_order'
    sql = "select order_type, status, dt from %s where \
        phone='%s' and status<%s"%(table, phone, OrderStatus.toeval)
    anylist = self.db.query(sql)
    
    if anylist is not None and len(anylist) > 0:
      self.write({'status_code':201, 
        'error_msg':u'亲，您有未完成的订单哦，请待完成后再预约新的订单~'})
      return True

    return False
   
  def process_booking_order(self, phone, order_id):
    # serialize to thrift obj and send to redis
    path = Path()
    path.from_city  = self.get_argument('from_city').encode('utf-8')
    path.from_place = self.get_argument('from_place').encode('utf-8')
    path.to_city  = self.get_argument('to_city').encode('utf-8')
    path.to_place = self.get_argument('to_place').encode('utf-8')

    path.from_lat = float(self.get_argument('from_lat'))
    path.from_lng = float(self.get_argument('from_lng'))
    path.to_lat = float(self.get_argument('to_lat'))
    path.to_lng = float(self.get_argument('to_lng'))

    order = Order()
    order.id = int(order_id)
    order.path = path
    order.phone = phone
    order.cartype = OrderType.booking
    order.number = int(self.get_argument('person_num'))
    order.price = int(self.get_argument('total_price'))
    order.start_time = self.get_argument('start_time')
    order.time = int(time.time())

    thrift_obj = serialize(order)
    
    pipe = self.r.pipeline()
    pipe.hset(options.order_rm, order_id, thrift_obj)
    pipe.lpush(options.order_rq, order_id)
    pipe.execute()



# /cancel_order
class CancelOrderHandler(BaseHandler):
  @base.authenticated
  #def get(self):
  def post(self):
    order_id = self.get_argument("order_id")
    
    table = 'cardb.t_order'
    sql = "select order_type, status, coupon_id from %s \
        where id = %s limit 1"%(table, order_id)
    obj = self.db.get(sql)

    # not booking order 
    if obj.order_type != OrderType.booking:
      # if order notpay, discard
      if obj.status == OrderStatus.notpay:
        self.discard_notpush_order(order_id, obj.coupon_id)
        self.write({'status_code':200, 'error_msg':''})
        return
      # after payed, cancel push
      if self.cancel_pushed_order(order_id, obj.coupon_id):
        self.write({'status_code':200, 'error_msg':''})
        return
      #self.write({'status_code':201, 'error_msg':'failed to cancel'})
      self.write({'status_code':201, \
          'error_msg':u'您的订单已经被司机接单了，取消失败，请联系客服'})
      return

    # booking order
    if obj.order_type == OrderType.booking:
      # pushed, but not confirmed or payed
      if obj.status == OrderStatus.notpay: 
        if self.cancel_pushed_order(order_id, obj.coupon_id):
          self.write({'status_code':200, 'error_msg':''})
        else:
          self.write({'status_code':201, \
            'error_msg':u'您的订单刚刚被司机接单了，如果确定取消，请重试'})
        return
      # confirmed, but not payed
      if status == OrderStatus.confirm: 
        self.cancel_confirmed_order(order_id, coupon_id)
        return

    self.write({'status_code':201, 'error_msg':u'这种情况不该发生'})

  def cancel_confirmed_order(self, order_id, coupon_id):
    table = 'cardb.t_order'
    sql = "select phone, driver, poolorder_id from %s where id=%s"%(table, order_id)
    obj = self.db.get(sql)

    # fetch poolorder info, booking order is one to one map to poolorder
    if obj.poolorder_id == 0:
      self.write({'status_code':201, 'error_msg':u'取消失败，未找到对应的司机接单信息'})
      return

    # cancel poolorder
    sql = "update %s set status=%s where id=%s"%(table, POStatus.cancel, obj.poolorder_id)
    self.db.execute(sql)

    # cancel this order
    self.discard_notpush_order(order_id, coupon_id)

    # push cancel message to driver
    pushmsg = Message()
    pushmsg.template_type = TempType.notify
    pushmsg.push_type = PushType.one
    pushmsg.app_type = AppType.driver
    pushmsg.title = 'cancel_booking_poolorder'
    
    jdict = { 'title': 'cancel_booking_poolorder',
        'user_phone': obj.phone,
        'poolorder_id': obj.poolorder_id
        }
    pushmsg.content = json.dumps(jdict)
    pushmsg.target = [obj.driver]
      
    thrift_obj = serialize(pushmsg)
    self.r.lpush(options.queue, thrift_obj)
   
    # result
    self.write({'status_code':200, 'error_msg':''})

  def cancel_pushed_order(self, order_id, coupon_id):
    # try cancel payed order
    ret = order_util.CancelOrder(self.r, order_id)

    if ret == 1: # success
      # will not send a canceled message, when driver confirm, get a canceled result
      table = 'cardb.t_order'
      sql = "update %s set status=%s where id=%s"%(table, OrderStatus.cancel, order_id)
      self.db.execute(sql)

      # restore coupon_id status
      if coupon_id != 0:
        table = 'cardb.t_coupon'
        sql = "update %s set status=%s where id=%s"%(table, CouponStatus.normal, coupon_id)
        self.db.execute(sql)

    # result
    return (ret == 1) 

  def discard_notpush_order(self, order_id, coupon_id):
    table = 'cardb.t_order'
    sql = "update %s set status=%s where id=%s"%(table, OrderStatus.discard, order_id)
    self.db.execute(sql)

    if coupon_id != 0:
      table = 'cardb.t_coupon'
      sql = "update %s set status=%s where id=%s"%(table, CouponStatus.normal, coupon_id)
      self.db.execute(sql)



# /read_confirmed_order
class ReadConfirmedOrderHandler(BaseHandler):
  @base.authenticated
  #def get(self):
  def post(self): # TODO: check api
    driver = self.get_argument('driver_phone')
    order_id = self.get_argument('order_id')
    is_confirm = self.get_argument('is_confirm')

    table = 'cardb.t_driver'
    sql = "select name, carno from %s where phone='%s' limit 1"%(table, driver)
    obj = self.db.get(sql)

    msg = {
        'status_code':200,
        'error_msg': '',
        'driver_phone': driver,
        'driver_name': obj.name,
        'driver_carno': obj.carno,
        'order_id': int(order_id),
        'is_confirm': int(is_confirm)
        }
    self.write(msg)


# /get_confirmed_driver
class GetConfirmedDriverHandler(BaseHandler):
  @base.authenticated
  def post(self):
    order_id = self.get_argument('order_id')
    
    table = 'cardb.t_order'
    sql = "select driver from %s where id=%s limit 1"%(table, order_id)
    obj = self.db.get(sql)

    if obj is None:
      self.write({'status_code':201, 'error_msg':''})
      return

    driver = obj.driver
    if driver == '-':
      self.write({'status_code':201, 'error_msg':'no available driver'})
      return

    table = 'cardb.t_driver'
    sql = "select name, carno from %s where phone='%s' limit 1"%(table, driver)
    obj = self.db.get(sql)

    msg = {
        'status_code':200,
        'error_msg': '',
        'driver_phone': driver,
        'driver_name': obj.name,
        'driver_carno': obj.carno
        }
    self.write(msg)
