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

    price = int(from_dist) + int(to_dist) + person_num * 10 + hour

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

    # select coupon from mysql
    table = 'cardb.t_coupon'
    sql = "select id, ctype, price, limit, deadline \
        from %s where phone='%s' and status=%s"%(table, phone, CouponStatus.normal)
    obj = self.db.query(sql)

    # coupon list json
    clist = [{'coupon_id':coupon.id,
          'coupon_desc':coupon.ctype,
          'coupon_price':coupon.price,
          'coupon_limit':coupon.limit,
          'coupon_deadline':coupon.deadline
          } for coupon in obj ]

    # return result
    msg = {
        "status_code":200,
        "coupon_num": len(obj),
        "coupon_infos":
        [
          { "coupon_id":123,
            "coupon_desc":"专车",
            "coupon_price":20,
            "coupon_limit":50,
            "coupon_deadline":"2015-01-31"
            }
          ]
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
class ReadConfirmedOrder(BaseHandler):
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


# ========================================
# callback

# /alipay_notify
class AlipayNotifyHandler(BaseHandler):
  def post(self):
    data = self.get_argument('notify_data')
    sign = self.get_argument('sign')

    # verify request is securety
    if not self.verify_sign(data, sign):
      self.write('failed')
      return

    if not self.verify_source():
      self.write('failed')
      return

    # parse xml notify_data
    try:
      root = ET.fromstring(data)

      # check trade is successful
      trade_status = root.find('trade_status').text
      if trade_status != 'TRADE_FINISHED' or trade != 'TRADE_SUCCESS':
        self.write('failed')
        return

      # record information
      trade_no = root.find('trade_no').text
      order_id = root.find('out_trade_no').text
      buyer = root.find('buyer_email').text
      seller = root.find('seller_email').text
      price = root.find('total_fee').text

      # insert into mysql
      table = 'cardb.t_payment'
      sql = "insert into %s \
          (pay_id, order_id, price, status, buyer, seller, extra_info, dt)\
          values (%s, %s, '%s', %s, %s, '%s', '%s', '', null)"\
          %(trade_no, order_id, price, 0, buyer, seller)
      self.db.execute(sql)

      # push order to scheduler
      self.process(order_id, trade_no, price)

      # return result
      self.write('success')

    except Exception, e:  # parse xml exception
      print 'error', e
      self.write('failed')

  def verify_sign(self, data, sign):
    sign_str = build_sign("notify_data=" + data, options.alipay_pubkey)
    if sign_str != sign:
      return False
    return True

  def verify_source(self):
    try:
      notify_id = self.get_argument('notify_id')
    except Exception, e:
      notify_id = ''
      print 'notify id is empty'
    if len(notify_id) == 0:
      return True

    url = 'https://mapi.alipay.com/gateway.do'
    params = {
        'partner' : options.alipay.partner,
        'notify_id' : notify_id,
        'service' : 'notify_verify'
        }

    ret = urlopen(url, urlencode(params)).read()
    return (ret.lower().strip() == 'true')

  def build_sign(self, data, key):
    return ''

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
    self.r.hset(options.order_rm, order_id, thrift_obj)
    self.r.lpush(options.order_rq, order_id)


# /share +weixin
class ShareHandler(BaseHandler):
  def post(self):
    pass




