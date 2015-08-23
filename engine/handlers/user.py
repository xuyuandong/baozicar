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

    os = '-'
    version = '-'
    try:
      os = self.get_argument('os')
      version = self.get_argument('version')
    except Exception, e:
      app_log.info('old user version, no os/version arguments')

    name = self.get_argument('name')
    gender = self.get_argument('gender')
    name = name + gender
    app_log.info('phone=%s, name=%s', phone, name)

    # check authcode
    if authcode != self.r.get(options.authcode_rpf + phone):
      app_log.info('{"status_code":201, "error_msg":"auth code error"}')
      self.write({"status_code":201, "error_msg":u"验证码错误"})
      return

    # unique user profile mapping: phone -> (device, push_id, type)
    rkey = options.login_rpf + phone
    dobj = self.r.hgetall(rkey)
    rexist = (dobj is None) or (len(dobj) < 3)

    # first login bind and set map
    if (rexist) or (dev_id != dobj['device']) or (push_id != dobj['push']) \
        or (LoginType.user != int(dobj['t'])):
      # async bind push_id
      if not ( yield self.async_bind(phone, push_id) ):
        app_log.info('{"status_code":201, "error_msg":"bind push_id error"}')
        self.write({"status_code":201, "error_msg":u"未能绑定消息推送"})
        return

      # device <-> push_id is one one mapping 
      self.r.hmset(rkey, {'device':dev_id, 'push':push_id, 'name':name, 't':LoginType.user})

    # process logic for first time login
    if rexist:
      self.first_login_reward(phone, dev_id, name, os, version)

    # update os, version
    self.update_user_info(phone, dev_id, os, version)

    # return token
    token = self.set_secure_cookie(options.token_key, phone)
    self.write({'status_code':200, 'error_msg':'', 'token':token})

  @run_on_executor
  def async_bind(self, phone, push_id):
    ret1 = self.push.user.unbindAliasAll(phone)
    ret2 = self.push.user.bindAlias(phone, push_id)
    return (ret2['result'].upper() == 'OK')

  def first_login_reward(self, phone, dev_id, name, os, version):
    table = 'cardb.t_user'
    sql = "select id from %s where phone='%s' limit 1"%(table, phone)
    obj = self.db.get(sql)

    # not first time login
    if obj is not None:
      return False

    # insert into mysql
    sql = "insert into %s (phone, dev, name, image, os, version)\
        values ('%s', '%s', '%s', '', '%s', '%s')"\
        %(table, phone, dev_id, name, os, version)
    self.db.execute(sql)

    deadline = datetime.datetime.now() + datetime.timedelta(days = 30)
    # reward a normal coupon
    coupon = {'ctype': -1,
        'price': 5,
        'within': 0,
        'deadline': deadline.strftime('%Y-%m-%d'),
        'note': u'新用户乘车优惠'}
    coupon_id = base.uuid(phone)

    table = 'cardb.t_coupon'
    sql = "insert into %s (id, ctype, status, price, within, deadline, note, phone, code, dt) \
        values(%s, %s, %s, %s, %s, '%s', '%s', '%s', %s, null)" \
        %(table, coupon_id, coupon['ctype'], CouponStatus.normal, \
        coupon['price'], coupon['within'], coupon['deadline'], coupon['note'], phone, 0)
    self.db.execute(sql)
   
    # reward a fixed-price coupon
    coupon = {'ctype': -2,
        'price': 5,
        'within': 0,
        'deadline': deadline.strftime('%Y-%m-%d'),
        'note': u'首单拼车通乘券'}
    coupon_id = base.uuid(phone)

    table = 'cardb.t_coupon'
    sql = "insert into %s (id, ctype, status, price, within, deadline, note, phone, code, dt) \
        values(%s, %s, %s, %s, %s, '%s', '%s', '%s', %s, null)" \
        %(table, coupon_id, coupon['ctype'], CouponStatus.normal, \
        coupon['price'], coupon['within'], coupon['deadline'], coupon['note'], phone, 0)
    self.db.execute(sql)

    # result
    return True

  def update_user_info(self, phone, dev_id, os, version):
    table = 'cardb.t_user'
    sql = "select os, version from %s where phone='%s' limit 1"%(table, phone)
    obj = self.db.get(sql)

    if (obj is not None): # and (obj.os != os or obj.version != version):
      current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      sql = "update %s set dev='%s', os='%s', version='%s', dt='%s' \
      where phone='%s'"%(table, dev_id, os, version, current_time, phone)
      self.db.execute(sql)



# /save_profile
class SaveProfileHandler(BaseHandler):
  @base.authenticated
  #def get(self):
  def post(self):
    phone = self.current_user
    name = self.get_argument('name')
    gender = self.get_argument('gender')
    pass



# ========================================
# user coupon

# /get_coupon_list
class GetCouponListHandler(BaseHandler):
  @base.authenticated
  #def get(self):
  def post(self):
    phone = self.current_user

    # select coupon from mysql, with expired <N days coupon
    table = 'cardb.t_coupon'
    sql = "select id, ctype, status, price, within, deadline, note \
        from %s where phone='%s' and status != %s"%(table, phone, CouponStatus.used)
    obj = self.db.query(sql)

    # coupon list json
    clist = [{'coupon_id': coupon.id,
          'coupon_type': coupon.ctype,
          'coupon_desc': coupon.note,
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


# /exchange_coupon
class ExchangeCouponHandler(BaseHandler):
  #@base.authenticated
  #def get(self):
  def post(self):
    phone = self.get_argument("phone")
    code = self.get_argument("key")

    # get coupon info
    ckey = 'c_' + code
    coupon = self.r.hgetall(ckey)
    if not coupon:
      #self.write({'status_code':201, 'error_msg':'invalid coupon'})
      self.write({'status_code':201, 'error_msg':u'无效的优惠券兑换码'})
      return

    # check deadline or duration
    if len(coupon['deadline']) == 0:
      duration = int(coupon['duration'])
      deadline = datetime.datetime.now() + datetime.timedelta(days = duration)
      coupon['deadline'] = deadline.strftime('%Y-%m-%d')

    # check already exchange
    table = 'cardb.t_coupon'
    sql = "select id from %s where phone=%s and code=%s limit 1;"%(table, phone, code)
    obj = self.db.get(sql)
    if obj is not None:
      msg = {
          'status_code' : 200,
          'error_msg' : '',
          'coupon_info': {
            'coupon_id': obj.id,
            'coupon_type': int(coupon['ctype']),
            'coupon_desc' : coupon['note'],
            'coupon_price' : int(coupon['price']),
            'coupon_limit' : int(coupon['within']),
            'coupon_deadline': coupon['deadline'],
            },
          'is_new': False
          }
      self.write(msg)
      return

    # reduce coupon number
    if 0 > self.r.hincrby(ckey, 'num', -1):
      #self.write({'status_code':201, 'error_msg':'coupon exhausted'})
      self.write({'status_code':201, 'error_msg':u'优惠券被抢光了'})
      return

    # insert into mysql db
    coupon_id = base.uuid(phone)
    sql = "insert into %s (id, ctype, status, price, within, deadline, note, phone, code, dt) \
        values(%s, %s, %s, %s, %s, '%s', '%s', '%s', %s, null)" \
        %(table, coupon_id, coupon['ctype'], CouponStatus.normal, \
        coupon['price'], coupon['within'], coupon['deadline'], coupon['note'], phone, code)
    self.db.execute(sql)

    # result
    msg = {
        'status_code' : 200,
        'error_msg' : '',
        'coupon_info': {
          'coupon_id': coupon_id,
          'coupon_type': int(coupon['ctype']),
          'coupon_desc' : coupon['note'],
          'coupon_price' : int(coupon['price']),
          'coupon_limit' : int(coupon['within']),
          'coupon_deadline': coupon['deadline'],
          },
        'is_new': True
        }
    self.write(msg)


# ===================================================

# /get_order_list
class GetOrderListHandler(BaseHandler):
  @base.authenticated
  #def get(self):
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
        OLType.booked: 'and status<=%s'%(OrderStatus.confirm), # wait or confirm
        OLType.toeval: 'and status=%s'%(OrderStatus.toeval), # toeval
        OLType.done: 'and status=%s'%(OrderStatus.toeval),   # done
        OLType.all:  ''
        }
    condition = typefilter.get(int(oltype))

    # select orders
    sql = "select id, order_type, status, start_time, num, \
        from_city, from_place, to_city, to_place, price, coupon_price,\
        dt from %s where phone='%s' %s"%(table, phone, condition)
    try:
      objlist = self.db.query(sql)
    except Exception, e:
      app_log.error('exception %s', e)
      objlist = []

    # order list json
    olist = [{
      'order_id': obj.id,
      'order_date':obj.dt.strftime("%Y-%m-%d %H:%M:%S"),
      'order_type':obj.order_type,
      'order_status':obj.status,
      'start_time':obj.start_time,
      'person_num':obj.num,
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
          "order_count":len(olist),
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


