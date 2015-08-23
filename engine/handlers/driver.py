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

###################### coding comment ########################
# status_code: 200 OK 201 Failed
# driver status:  0 online 1 offline 2 other
# poolorder_type: 0 carpool 1 specialcar 2 all
# poolorder_status: 0 wait 1 confirm 2 ongoing 3 done 4 cancel
##############################################################
from base import LoginType, TempType, PushType, AppType, OrderType, OrderStatus, OLType
from base import POType, POStatus, CouponStatus, DriverStatus
from base import BaseHandler
from ttypes import Path, Order, PoolOrder, Message


# /login_driver
class DriverLoginHandler(BaseHandler):
  executor = ThreadPoolExecutor(4)

  @tornado.web.asynchronous
  @tornado.gen.coroutine
  #def get(self):
  def post(self):
    phone = self.get_argument('phone')
    authcode = self.get_argument('authcode')
    dev_id = self.get_argument('dev_id')
    push_id = self.get_argument('push_id')
    
    app_log.info('driver phone=%s, push_id=%s', phone, push_id)

    # check authcode
    if authcode != self.r.get(options.authcode_rpf + phone):
      #self.write({"status_code":201, "error_msg":"auth code error"})
      self.write({"status_code":201, "error_msg":u"验证码错误"})
      return
    
    # unique user profile mapping: phone -> (device, push_id, type)
    rkey = options.login_rpf + phone
    dobj = self.r.hgetall(rkey)
    rexist = (dobj is None) or (len(dobj) < 3)

    # first login bind and set map
    if (rexist) or (dev_id != dobj['device']) or (push_id != dobj['push']) \
        or (LoginType.driver != int(dobj['t'])):
      # async bind push_id
      if not ( yield self.async_bind(phone, push_id) ):
        #self.write({"status_code":201, "error_msg":"bind push_id error"})
        self.write({"status_code":201, "error_msg":u"未能绑定消息推送"})
        return
      # device <-> push_id is one one mapping 
      self.r.hmset(rkey, {'device':dev_id, 'push':push_id, 't':LoginType.driver})

    # update status, join scheduler
    self.join_scheduler(phone)

  @run_on_executor
  def async_bind(self, phone, push_id):
    ret1 = self.push.driver.unbindAliasAll(phone)
    ret2 = self.push.driver.bindAlias(phone, push_id)
    app_log.info('bind %s %s', ret1, ret2)
    return (ret2['result'].upper() == 'OK')

  def join_scheduler(self, phone):
    # select driver information
    table = 'cardb.t_driver'
    sql = "select name, from_city, to_city, status, priority \
        from %s where phone='%s' limit 1"%(table, phone)
    obj = self.db.get(sql)

    # check driver information
    if obj is None or len(obj) == 0:
      app_log.info('driver is not registered in our sysytem')
      #self.write({'status_code':201, 'error_msg':'driver is not registered in our system'})
      self.write({'status_code':201, 'error_msg':u'该号码尚未通过司机信息审核'})
      return
    
    driver_status = DriverStatus.busy
    if obj.status != DriverStatus.busy:
      # when login, make sure driver status is offline
      driver_status = DriverStatus.offline

      sql = "update %s set status=%s where phone='%s'"%(table, DriverStatus.offline, phone)
      self.db.execute(sql)
      # remove from scheduler
      path_rpq = options.driver_rpq + '-'.join([obj.from_city, obj.to_city])
      self.r.zrem(path_rpq, phone)
      #self.r.zadd(path_rpq, phone, obj.priority)

    # access token
    token = self.set_secure_cookie(options.token_key, phone)
    # result
    msg = { 'status_code':200, 
        'error_msg':'', 
        'token':token,
        'name':obj.name, 
        'from_city':obj.from_city, 
        'to_city':obj.to_city,
        'driver_status':driver_status
        }
    #app_log.info(msg)
    self.write(msg)

# =============================================

# /get_driver_status
class GetDriverStatusHandler(BaseHandler):
  @base.authenticated
  def post(self):
    phone = self.current_user
    
    table = 'cardb.t_driver'
    sql = "select from_city, to_city, status, priority \
        from %s where phone='%s' limit 1"%(table, phone)
    obj  = self.db.get(sql)

    if obj is None:
      self.write({'status_code':201, 'error_msg':u'查无此司机'})
      return

    msg = {'status_code': 200, 
           'error_msg': '', 
           'status': obj.status, 
           'from_city': obj.from_city,
           'to_city': obj.to_city
          }
    self.write(msg)


# /change_driver_status
class DriverChangeStatusHandler(BaseHandler):
  @base.authenticated
  #def get(self):
  def post(self):
    phone = self.current_user
    status = int(self.get_argument('status'))
    app_log.info('phone=%s, status=%s', phone, status)   
 
    # check target status 
    if status == DriverStatus.busy:
      self.write({'status_code':201, 'error_msg':'you cannot change to busy status'})
      return

    # update mysql driver status
    table = 'cardb.t_driver'
    sql = "select from_city, to_city, status, priority \
        from %s where phone='%s' limit 1"%(table, phone)
    route  = self.db.get(sql)
    
    # check current status
    if route.status == DriverStatus.busy:
      #self.write({'status_code':201, 'error_msg':'you do not finish your job, cannot change status'})
      self.write({'status_code':201, 'error_msg':u'您有未完成的订单，不能改变状态'})
      return

    # update status
    sql = "update %s set status=%s where phone='%s'"%(table, status, phone)
    self.db.execute(sql)

    # update redis scheduler
    path_rpq = options.driver_rpq + '-'.join([route.from_city, route.to_city])
    result = 0
    if status == DriverStatus.offline: # online -> offline
      result = self.r.zrem(path_rpq, phone)
    else:  # offline -> online
      result = self.r.zadd(path_rpq, phone, route.priority)

    # return result
    if result == 1:
      self.write({'status_code':200, 'error_msg':''})
    else:
      #self.write({'status_code':201, 'error_msg':'already in target status'})
      self.write({'status_code':201, 'error_msg':u'系统错误，已经是该状态'})


# /change_driver_route
class DriverChangeRouteHandler(BaseHandler):
  @base.authenticated
  #def get(self):
  def post(self):
    phone = self.current_user
    from_city = self.get_argument('from_city')
    to_city = self.get_argument('to_city')

    # select priority
    table = 'cardb.t_driver'
    sql = "select from_city, to_city, status, priority from %s \
           where phone='%s' limit 1"%(table, phone)
    obj = self.db.get(sql)

    if obj is None:
      self.write({'status_code':201, 'error_msg':u'查无此司机'})
      return

    # check current status
    if obj.status == DriverStatus.busy:
      #self.write({'status_code':201, 'error_msg':'you do not finish your job, cannot change route'})
      self.write({'status_code':201, 'error_msg':u'您有未完成的订单，不能改变路线'})
      return

    # check same route
    if obj.from_city == from_city and obj.to_city == to_city:
      self.write({'status':200, 'error_msg':''})
      return

    # update mysql
    sql = "update %s set from_city='%s', to_city='%s' where phone='%s'"\
        %(table, from_city, to_city, phone)
    self.db.execute(sql)

    # check whether update redis
    if obj.status == DriverStatus.offline:
      self.write({'status':200, 'error_msg':''})
      return

    # update redis
    old_path_rpq = options.driver_rpq + '-'.join([obj.from_city, obj.to_city])
    ret = self.r.zrem(old_path_rpq, phone)
    app_log.info('zrem %s ret=%s', old_path_rpq, ret)
    
    new_path_rpq = options.driver_rpq + '-'.join([from_city, to_city])
    ret = self.r.zadd(new_path_rpq, phone, obj.priority)
    app_log.info('zadd %s ret=%s', new_path_rpq, ret)

    # return result
    self.write({'status':200, 'error_msg':''})



# /get_poolorder_list
class GetPoolOrderListHandler(BaseHandler):
  @base.authenticated
  #def get(self):
  def post(self):
    phone = self.current_user
    date = self.get_argument('date')
    poltype = self.get_argument('poolorder_list_type')

    # choose table
    threeDayAgo = datetime.datetime.now() - datetime.timedelta(days=2)
    dstday = time.strptime(threeDayAgo.strftime("%Y%m%d"), "%Y%m%d")
    curday = time.strptime(date, "%Y%m%d")

    table = 'cardb.t_poolorder'
    if curday < dstday:
      table = table + "_" + date

    # select mysql
    condition = "and po_type='%s'"%(poltype) if int(poltype) < 2 else ""

    sql = "select id, po_type, status, from_city, to_city, price, \
        dt, original_price, multiply\
        from %s where phone='%s' %s order by dt"%(table, phone, condition)
    try:
      objlist = self.db.query(sql)
    except Exception, e:
      app_log.error('exception %s', e)
      objlist = []

    # poolorder list
    polist = [{
       'poolorder_id': obj.id,
       'poolorder_date': obj.dt.strftime("%Y-%m-%d %H:%M:%S"),
       'poolorder_type': obj.po_type,
       'poolorder_status': obj.status,
       'from_city': obj.from_city,
       'to_city': obj.to_city,
       'poolorder_price': obj.price,
       'original_price': obj.original_price,
       'multiply': obj.multiply
      } for obj in objlist ]

    # return result
    msg = {
        'status_code':200,
        'error_msg':'',
        'poolorder_count':len(polist),
        'poolorder_infos': polist
        }
    self.write(msg)


# /get_poolorder_detail
class GetPoolOrderDetailHandler(BaseHandler):
  @base.authenticated
  #def get(self):
  def post(self):
    phone = self.current_user
    date = self.get_argument('date')
    poid = self.get_argument('poolorder_id')

    # choose table
    threeDayAgo = datetime.datetime.now() - datetime.timedelta(days=2)
    dstday = time.strptime(threeDayAgo.strftime("%Y%m%d"), "%Y%m%d")
    curday = time.strptime(date, "%Y%m%d")

    table = 'cardb.t_poolorder'
    if curday < dstday:
      table = table + "_" + date

    # select sub-orders from mysql
    sql = "select po_type, status, from_city, to_city, price, orders, \
        last_modify, original_price, multiply\
        from %s where id=%s limit 1"%(table, poid)
    obj = self.db.get(sql)

    # select user info from sub-orders
    table = 'cardb.t_order'
    if curday < dstday:
      table = table + "_" + date
    sql = "select phone, name, from_place, to_place, start_time, num, msg\
          from %s where poolorder_id=%s"%(table, poid)
    orders = self.db.query(sql)

    # result 
    uinfos = [{
        'name': order.name,
        'phone': order.phone,
        'from_place': order.from_place,
        'to_place': order.to_place,
        'start_time': order.start_time,
        'person_num': order.num,
        'extra_msg': order.msg
        } for order in orders ]

    # return result
    msg = {
        'status_code':200,
        'error_msg':'',
        'poolorder_detail':{
          'poolorder_id':poid,
          'poolorder_date':date,
          'poolorder_type':obj.po_type,
          'poolorder_status':obj.status,
          'from_city':obj.from_city,
          'to_city':obj.to_city,
          'total_price':obj.price,
          'original_price': obj.original_price,
          'multiply': obj.multiply,
          'user_infos':uinfos,
          'poolorder_start_time':obj.last_modify.strftime("%Y-%m-%d %H:%M:%S")
          }
        }
    self.write(msg);



# /get_driver_data
class GetDriverDataHandler(BaseHandler):
  @base.authenticated
  def post(self):
    phone = self.current_user

    date = self.get_argument('date')
    today = time.strptime(date, '%Y%m%d')
    today_str = time.strftime('%Y-%m-%d %H:%M:%S', today)

    # today data
    table = 'cardb.t_poolorder'
    sql = "select sum(price) as income, count(1) as ponum \
        from %s where phone='%s' and status=%s \
        and last_modify>'%s'"%(table, phone, POStatus.done, today_str)
    obj = self.db.get(sql)

    # all data
    table = 'cardb.t_driver_data'
    sql = "select income, ponum from %s where phone='%s'"%(table, phone)
    all = self.db.get(sql)
    
    # check
    if obj is None or all is None:
      msg = {'status_code':200,
          'error_msg':'',
          'income_today':0,
          'ponum_today':0,
          'income_all':0,
          'ponum_all':0
          }
      self.write(msg)
      return

    # result
    msg = {'status_code':200,
        'error_msg':'',
        'income_today':obj.income,
        'ponum_today':obj.ponum,
        'income_all':all.income,
        'ponum_all':all.ponum
        }

    self.write(msg)
