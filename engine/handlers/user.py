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
from base import TempType, PushType, AppType, OrderType, OrderStatus, OLType
from base import POType, POStatus, CouponStatus, DriverStatus
from base import BaseHandler
from ttypes import Path, Order, Message


# /login_user
class UserLoginHandler(BaseHandler):
  executor = ThreadPoolExecutor(4)

  @tornado.web.asynchronous
  @tornado.gen.coroutine
  def post(self):
    phone = self.get_argument("phone")
    authcode = self.get_argument("authcode")
    dev_id = self.get_argument("dev_id")
    push_id = self.get_argument('push_id')

    # check authcode
    if authcode != self.r.get('auth_' + phone):
      self.write({"status_code":201, "error_msg":"auth code error"})
      return

    # async bind push_id
    if not ( yield self.async_bind(phone, push_id) ):
      self.write({"status_code":201, "error_msg":"bind push_id error"})
      return

    # unique (phone - device) (device - pushid) mapping
    self.r.hset(options.login_rm, phone, dev_id)
    self.r.hset(options.push_rm, phone, push_id)

    # insert into mysql
    table = 'cardb.t_user'
    sql = "insert into %s (phone, dev, name, image)\
        values ('%s', '%s', '', '') \
        on duplicate key update dev='%s'"%(table, phone, dev_id, dev_id)
    self.db.execute(sql)

    # return token
    token = self.set_secure_cookie(options.token_key, phone)
    self.write({'status_code':200, 'error_msg':'', 'token':token})

  @run_on_executor
  def async_bind(self, phone, push_id):
    ret1 = self.push.user.unbindAliasAll(phone)
    #if ret1['result'].upper() != 'OK':
    #  app_log.info('unbind %s failed'%(phone))
    #  return False
    ret2 = self.push.user.bindAlias(phone, push_id)
    return (ret2['result'].upper() == 'OK')


# /save_profile
class SaveProfileHandler(BaseHandler):
  @base.authenticated
  def post(self):
    pass


# /query_path
class QueryPathHandler(BaseHandler):
  #@base.authenticated
  def post(self): # TODO: check api
    from_city = self.argument('from_city')

    table = 'cardb.t_path'
    sql = "select to_city from %s where from_city='%s';"%(table, from_city)
    objlist = self.db.query(sql)

    result = [ obj.to_city for obj in objlist ]
    msg = {
        'status_code':200,
        'error_msg':'',
        'to_city_list':result
        }
    self.write(msg)


# /query_price
class QueryPriceHandler(BaseHandler):
  #@base.authenticated
  def post(self):
    from_city = self.get_argument('from_city')
    to_city = self.get_argument('to_city')

    from_dist = self.get_argument('from_distance')
    to_dist = self.get_argument('to_distance')

    person_num = self.get_argument('person_num')
    hour = time.localtime().tm_hour

    #price = int(from_dist) + int(to_dist) + int(person_num) * 10 + (hour)
    price = 0.02
    msg = {
        'status_code': 200,
        'error_msg': '',
        'price': price
        }
    self.write(msg)

# ========================================
# user coupon

# /get_coupon_list
class GetCouponListHandler(BaseHandler):
  @base.authenticated
  def post(self):
    phone = self.current_user

    # select coupon from mysql, with expired <N days coupon
    table = 'cardb.t_coupon'
    sql = "select id, ctype, status, price, within, deadline \
        from %s where phone='%s' and status != %s"%(table, phone, CouponStatus.used)
    obj = self.db.query(sql)

    # coupon list json
    clist = [{'coupon_id': coupon.id,
          'coupon_desc': coupon.ctype,
          'coupon_status': coupon.status,
          'coupon_price': coupon.price,
          'coupon_limit': coupon.within,
          'coupon_deadline': coupon.deadline
          } for coupon in obj ]

    # return result
    msg = {
        "status_code":200,
        "coupon_num": len(obj),
        "coupon_infos": clist
        }
    self.write(msg)


# /select_coupon
class SelectCouponHandler(BaseHandler):
  @base.authenticated
  def post(self):
    order_id = self.get_argument('order_id')
    coupon_id = self.get_argument('coupon_id')
    coupon_price = self.get_argument('coupon_price')

    table = 'cardb.t_order'
    sql = "update %s set coupon_id='%s', coupon_price=%s \
        where id=%s"%(table, coupon_id, coupon_price, order_id)
    self.db.execute(sql)

    self.write({'status_code':200, 'error_msg':''})


# /exchange_coupon
class ExchangeCouponHandler(BaseHandler):
  #@base.authenticated
  def post(self):
    phone = self.get_argument("phone")
    code = self.get_argument("key")
    ckey = 'c_' + code

    # get coupon info
    coupon = self.r.hgetall(ckey)
    if not coupon:
      self.write({'status_code':201, 'error_msg':'invalid coupon'})
      return

    # check already exchange
    table = 'cardb.t_coupon'
    sql = "select id from %s where phone=%s and code=%s limit 1;"%(table, phone, code)
    obj = self.db.get(sql)
    if obj.id is not None:
      msg = {
          'status_code' : 200,
          'error_msg' : '',
          'coupon_info': {
            'coupon_id': obj.id,
            'coupon_desc' : '',
            'coupon_price' : coupon['price'],
            'coupon_limit' : coupon['limit'],
            'coupon_deadline': coupon['deadline'],
            }
          }
      self.write(msg)
      return

    # reduce coupon number
    left = self.r.hincrby(ckey, 'num', -1)
    if left < 0:
      self.write({'status_code':201, 'error_msg':'coupon exhausted'})
      return

    # insert into mysql db
    sql = "insert into %s (ctype, status, price, within, deadline, phone, code, dt) \
        values(%s, %s, %s, %s, '%s', '%s', %s, null)" \
        %(table, coupon['ctype'], CouponStatus.normal, \
        coupon['price'], coupon['limit'], coupon['deadline'], phone, code)
    self.db.execute(sql)

    # coupon unique id generator
    obj = self.db.get("select last_insert_id() as id")
    coupon_id = obj.id

    msg = {
        'status_code' : 200,
        'error_msg' : '',
        'coupon_info': {
          'coupon_id': coupon_id,
          'coupon_desc' : '',
          'coupon_price' : coupon['price'],
          'coupon_limit' : coupon['limit'],
          'coupon_deadline': coupon['deadline'],
          }
        }
    self.write(msg)


# ========================================
# user order

# /submit_order
class SubmitOrderHandler(BaseHandler):
  @base.authenticated
  def post(self):
    phone = self.current_user

    order_type = self.get_argument("order_type")

    from_city = self.get_argument("from_city")
    from_place = self.get_argument("from_place")
    to_city = self.get_argument("to_city")
    to_place = self.get_argument("to_place")

    name = self.get_argument("name")
    person_num = self.get_argument("person_num")
    price = self.get_argument("total_price")

    pay_id = 0 #self.get_argument('pay_id')
    fact_price = 0 #self.get_argument("fact_price")
    coupon_id = '-' #self.get_argument("coupon_id")
    coupon_price = 0 #self.get_argument("coupon_price")

    # special car argument
    extra_msg = ''
    start_time = ''
    if int(order_type) == OrderType.special:
      extra_msg = self.get_argument('extra_msg')
      start_time = self.get_argument('start_time')

    # insert into mysql db
    table = 'cardb.t_order'
    sql = "insert into %s (order_type, status, phone, name, start_time,\
           from_city, from_place, to_city, to_place, num, msg,\
           pay_id, price, fact_price, coupon_id, coupon_price, dt) \
           values(%s, %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s',\
           %s, '%s', %s, %s, %s, '%s', %s, null)"\
           %(table, order_type, OrderStatus.notpay, phone, name, start_time,
               from_city, from_place, to_city, to_place, person_num, extra_msg,
               pay_id, price, fact_price, coupon_id, coupon_price)
    self.db.execute(sql)

    # order unique id generator
    obj = self.db.get("select last_insert_id() as id")
    order_id = obj.id

    # return result
    msg = {'status_code':200,
           'error_msg':'',
           'order_id':order_id
           }
    self.write(msg)


# /cancel_order
class CancelOrderHandler(BaseHandler):
  @base.authenticated
  def post(self):
    order_id = self.get_argument("order_id")

    ret = order_util.CancelOrder(self.r, order_id)

    if ret == 1: # success
      # will not send a canceled message, when driver confirm, get a canceled result

      table = 'cardb.t_order'
      sql = "update %s set status=%s where id=%s"%(table, OrderStatus.cancel, order_id)
      self.db.execute(sql)

      self.write({'status_code':200, 'error_msg':''})
    else:
      self.write({'status_code':201, 'error_msg':'failed to cancel'})


# /read_confirmed_order
class ReadConfirmedOrderHandler(BaseHandler):
  @base.authenticated
  def post(self): # TODO: check api
    driver = self.get_argument('driver')

    table = 'cardb.t_driver'
    sql = "select name, carno from %s where phone='%s'"%(table, driver)
    obj = self.db.get(sql)

    msg = {
        'status_code':200,
        'error_msg': '',
        'driver_phone': driver,
        'driver_name': obj.name,
        'driver_carno': obj.carno
        }
    self.write(msg)


# ===================================================

# /get_order_list
class GetOrderListHandler(BaseHandler):
  @base.authenticated
  def post(self):
    phone = self.current_user
    date = self.get_argument("date")

    # choose table
    threeDayAgo = datetime.datetime.now() - datetime.timedelta(days=2)
    dstday = time.strptime(threeDayAgo.strftime("%Y%m%d"), "%Y%m%d")
    curday = time.strptime(date, "%Y%m%d")

    table = 'cardb.t_order'
    if curday < dstday:
      table = table + "_" + date

    # get type filter
    oltype = self.get_argument("order_list_type")
    typefilter = {
        OLType.booked: 'and status<2', # wait or confirm
        OLType.toeval: 'and status=2', # toeval
        OLType.done: 'and status=3',   # done
        OLType.all:  ''
        }
    condition = typefilter.get(int(oltype))

    # select orders
    sql = "select id, order_type, status, start_time,\
        from_city, from_place, to_city, to_place, price, coupon_price,\
        dt from %s where phone='%s' %s"%(table, phone, condition)
    objlist = self.db.query(sql)

    # order list json
    olist = [{
      'order_id': obj.id,
      'order_date':obj.dt.strftime("%Y-%m-%d %H:%M:%S"),
      'order_type':obj.order_type,
      'order_status':obj.status,
      'start_time':obj.start_time,
      'from_city':obj.from_city,
      'from_place':obj.from_place,
      'to_city':obj.to_city,
      'to_place':obj.to_place,
      'total_price':obj.price,
      'coupon_price':obj.coupon_price
      } for obj in objlist ]

    # return result
    msg = {
          "status_code":200,
          "error_msg":"",
          "order_count":1,
          "order_infos":olist
        }
    self.write(msg)


# /get_order_detail
class GetOrderDetailHandler(BaseHandler):
  @base.authenticated
  def post(self):
    pass


# /submit_comment
class SubmitCommentHandler(BaseHandler):
  @base.authenticated
  def post(self):
    pass

