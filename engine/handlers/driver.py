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

    # check authcode
    if authcode != self.r.get(options.authcode_rpf + phone):
      #self.write({"status_code":201, "error_msg":"auth code error"})
      self.write({"status_code":201, "error_msg":u"验证码错误"})
      return

    # unique user profile mapping: phone -> (device, push_id)
    rkey = options.login_rpf + phone
    if dev_id != self.r.hget(rkey, 'device') or str(LoginType.driver) != self.r.hget(rkey, 't'):
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
    return (ret2['result'].upper() == 'OK')

  def join_scheduler(self, phone):
    app_log.info('driver phone: %s', phone)

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
    app_log.info(msg)
    self.write(msg)

# =============================================

# /change_driver_status
class DriverChangeStatusHandler(BaseHandler):
  @base.authenticated
  #def get(self):
  def post(self):
    phone = self.current_user
    status = int(self.get_argument('status'))
    
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
    sql = "select status, priority from %s where phone='%s' limit 1"%(table, phone)
    obj = self.db.get(sql)

    # check current status
    if obj.status == DriverStatus.busy:
      #self.write({'status_code':201, 'error_msg':'you do not finish your job, cannot change route'})
      self.write({'status_code':201, 'error_msg':u'您有未完成的订单，不能改变路线'})
      return

    # update mysql
    sql = "update %s set from_city='%s', to_city='%s' where phone='%s'"\
        %(table, from_city, to_city, phone)
    self.db.execute(sql)

    # update redis
    old_path_rpq = options.driver_rpq + '-'.join([to_city, from_city])
    path_rpq = options.driver_rpq + '-'.join([from_city, to_city])

    pipe = self.r.pipeline()
    pipe.zrem(old_path_rpq, phone)
    pipe.zadd(path_rpq, phone, obj.priority)
    pipe.execute()

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

    sql = "select id, po_type, status, from_city, to_city, price, dt\
        from %s where phone='%s' %s order by dt"%(table, phone, condition)
    try:
      objlist = self.db.query(sql)
    except Exception, e:
      app_log.error('exception %s', e)
      objlist = []

    # poolorder list
    polist = [{
       'poolorder_id': obj.id,
       'poolorder_date': base.UTC2CST(obj.dt),
       'poolorder_type': obj.po_type,
       'poolorder_status': obj.status,
       'from_city': obj.from_city,
       'to_city': obj.to_city,
       'poolorder_price': obj.price
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
    sql = "select po_type, status, from_city, to_city, price, orders\
        from %s where id=%s limit 1"%(table, poid)
    obj = self.db.get(sql)

    # select user info from sub-orders
    table = 'cardb.t_order'
    if curday < dstday:
      table = table + "_" + date
    orderids = obj.orders.split(',')

    sqls = [ "select phone, name, from_place, to_place, start_time, msg\
          from %s where id=%s"%(table, oid) for oid in orderids ]
    sql = " union all ".join(sqls) if len(orderids) > 1 else sqls[0]

    # query mysql
    try:
      orders = self.db.query(sql)
    except Exception, e:
      app_log.error('exception %s', e)
      orders = []

    # result 
    uinfos = [{
        'name': order.name,
        'phone': order.phone,
        'from_place': order.from_place,
        'to_place': order.to_place,
        'start_time': order.start_time,
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
          'user_infos':uinfos
          }
        }
    self.write(msg);



# /change_poolorder_status
class ChangePoolOrderStatusHandler(BaseHandler):
  @base.authenticated
  #def get(self):
  def post(self):
    phone = self.current_user

    # confirm->32bit string id, else->integer id
    poid = self.get_argument('poolorder_id')
    status = int(self.get_argument('status'))

    action = {
        POStatus.confirm: self.confirm,
        POStatus.unfreeze: self.unfreeze,
        POStatus.ongoing: self.ongoing,
        POStatus.done: self.done
        }
    # switch status to pick method
    if status in action:
      action.get(status)(phone, poid)
    else:
      self.write({'status_code':201, 'error_msg':'wrong action'})


  def confirm(self, phone, poid):
    # get poolorder
    postr = self.r.hget(options.poolorder_rm, poid)
    if postr is None or len(postr) == 0: # failed
      self.write({'status_code':201, \
          'temp_poolorder_id': poid, 'is_new':True, \
          'error_msg':u'该订单已取消或已被其他司机接单了'})
          #'error_msg':'already canceled by user or confirmed by other driver'})
      return

    # get orders from poolorder thrift object
    poolorder = PoolOrder()
    poolorder = deserialize(poolorder, postr)

    # path = from & to city
    from_city = poolorder.order_list[0].path.from_city
    to_city = poolorder.order_list[0].path.to_city
    path = '-'.join([from_city, to_city])

    # lock the driver
    priority = self.__confirm_lock_driver(phone, path) 
    if priority < 0: # already try confirm in another poolorder
      self.write({'status_code':201, 'is_new':True, \
          'error_msg':u'您已经再抢其他订单了，请稍后再试'})
          #'error_msg':'you are trying confirm another poolorder'})
      return

    # get sub-orders infomation
    orderids = [ str(order.id) for order in poolorder.order_list ]
    userphones = [order.phone for order in poolorder.order_list ]
    total_price = poolorder.subsidy + sum([order.price for order in poolorder.order_list])

    # try confirm
    ret = order_util.ConfirmOrder(self.r, orderids)
    if ret is False: # confirm failed
      self.__confirm_unlock_driver(phone, path, priority)
      self.write({'status_code':201, 'is_new':True, \
          'temp_poolorder_id':poid, \
          'error_msg':u'该订单已取消或已被其他司机接单了'})
          #'error_msg':'already canceled by user or confirmed by other driver'})
      return

    # successful confirm: ########
      
    # weather to remove driver from sheduler queue
    status = POStatus.confirm if (poolorder.cartype == POType.special) else POStatus.ongoing
    self.__confirm_update_driver_status(phone, priority, path, status)

    # insert poolorder into mysql
    poolorder_id = base.uuid(phone)

    table = 'cardb.t_poolorder'
    sql = "insert into %s \
        (id, po_id, po_type, status, price, phone, from_city, to_city, orders, subsidy, sstype, dt) \
        values(%s, '%s', %s, %s, %s, '%s', '%s', '%s', '%s', %s, %s, null)"\
        %(table, poolorder_id, poid, poolorder.cartype, status,
        total_price, phone, from_city, to_city, ','.join(orderids),
        poolorder.subsidy, poolorder.sstype)
    self.db.execute(sql)

    # update orders status
    self.__confirm_update_order_status(poolorder.order_list)

    # push response message to users
    self.__confirm_push_message(phone, poolorder.order_list)

    # return result
    self.write({'status_code':200, 'is_new':True, 'error_msg':'', \
        'poolorder_id':poolorder_id, 'temp_poolorder_id':poid })


  def __confirm_lock_driver(self, phone, path):
    driver_rpq = options.driver_rpq + path
    priority = self.r.zscore(driver_rpq, phone)
    ret = self.r.zrem(driver_rpq, phone)
    return priority if (ret > 0) else -1

  def __confirm_unlock_driver(self, phone, path, priority):
    driver_rpq = options.driver_rpq + path
    self.r.zadd(driver_rpq, phone, priority)
      

  def __confirm_update_driver_status(self, phone, priority, path, poolorder_status):
    path_obj = options.path_rpf + path
    driver_num = self.r.hget(path_obj, 'driver_num')
    priority = priority + int(driver_num)
    
    table = 't_driver'
    if poolorder_status == POStatus.confirm:
      sql = "update %s set priority=%s where phone='%s'"%(table, priority, phone)
      self.db.execute(sql)
      
      driver_rpq = options.driver_rpq + path
      self.r.zadd(driver_rpq, phone, priority)

    else: # ongoing
      sql = "update %s set status=%s, priority=%s \
          where phone='%s'"%(table, DriverStatus.busy, priority, phone)
      self.db.execute(sql)

  def __confirm_update_order_status(self, order_list):
    table = 'cardb.t_order'
    order_condition = ','.join([str(order.id) for order in order_list])
    sql = "update %s set status=%s where id in (%s)"%(table, OrderStatus.confirm, order_condition)
    self.db.execute(sql)

  def __confirm_push_message(self, driver_phone, order_list):
    pushmsg = Message()
    pushmsg.template_type = TempType.notify
    pushmsg.push_type = PushType.one
    pushmsg.app_type = AppType.user
    pushmsg.title = 'confirm_poolorder'
    
    for order in order_list:
      jdict = { 'title': 'confirm_poolorder',
          'driver_phone': driver_phone,
          'order_id': order.id }
      pushmsg.content = json.dumps(jdict)
      pushmsg.target = [order.phone]
      
      thrift_obj = serialize(pushmsg)
      self.r.lpush(options.queue, thrift_obj)

  def unfreeze(self, phone, poid):
    table = 'cardb.t_poolorder'
    sql = "select from_city, to_city from %s where id=%s limit 1"%(table, poid)
    obj = self.db.get(sql)

    path_rpq1 = options.driver_rpq + '-'.join([obj.from_city, obj.to_city])
    path_rpq2 = options.driver_rpq + '-'.join([obj.to_city, obj.from_city])

    pipe = self.r.pipeline(transaction=False)
    ret = pipe.zrem(path_rpq1, phone).zrem(path_rpq2, phone).execute()

    if ret[0] + ret[1] > 0:
      table = 'cardb.t_driver'
      sql = "update %s set status=%s where phone='%s'"%(table, DriverStatus.busy, phone)
      self.db.execute(sql)

      sql = "update %s set status="
      self.write({'status_code':200, 'is_new':False, \
          'poolorder_id':poid, 'error_msg':''})
    else:
      self.write({'status_code':201, 'is_new':False, \
          'poolorder_id':poid, \
          'error_msg':'failed to unfreeze, driver is not available'})


  def ongoing(self, phone, poid):
    table = 'cardb.t_poolorder'
    sql = "update %s set status=%s where id=%s"%(table, POStatus.ongoing, poid)
    self.db.execute(sql)

    # TODO: push message to user

    self.write({'status_code':200, 'error_msg':'', 'is_new':False, 'poolorder_id':poid})

  def __ongoing_push_message(self, driver_phone, poid):
    # get sub-order ids
    table = 'cardb.t_poolorder'
    sql = "select orders from %s where id=%s limit 1"%(table, poid)
    obj = self.db.get(sql)

    orderids = obj.orders.split(',')
    
    # get user phones
    table = 'cardb.t_order'
    sqls = ["select id, phone from %s where id=%s"%(table, oid) for oid in orderids ]
    sql = " union all ".join(sqls) if len(orderids) > 1 else sqls[0]
    objlist = self.db.query(sql)

    # push messages
    pushmsg = Message()
    pushmsg.template_type = TempType.notify
    pushmsg.push_type = PushType.one
    pushmsg.app_type = AppType.user
    pushmsg.title = 'ongoing_poolorder'
    
    for order in objlist:
      jdict = { 'title': 'ongoing_poolorder',
          'driver_phone': driver_phone,
          'order_id': order.id }
      pushmsg.content = json.dumps(jdict)
      pushmsg.target = [order.phone]
      
      thrift_obj = serialize(pushmsg)
      self.r.lpush(options.queue, thrift_obj)


  def done(self, phone, poid):
    table = 'cardb.t_poolorder'
    # select orders from poolorder
    sql = "select status, orders from %s where id=%s limit 1"%(table, poid)
    obj = self.db.get(sql)

    # protect redo multiple times
    if obj.status == POStatus.done:
      self.write({'status_code':200, 'error_msg':'', 'is_new':False, 'poolorder_id':poid})
      return

    # update poolorder status
    sql = "update %s set status=%s where id=%s"%(table, POStatus.done, poid)
    self.db.execute(sql)
    
    orderids = obj.orders.split(',')
    # update order status
    table = 'cardb.t_order'
    order_condition = ','.join([str(oid) for oid in orderids])
    sql = "update %s set status=%s where id in (%s)"%(table, OrderStatus.toeval, order_condition)
    self.db.execute(sql)

    # select driver route and priority
    table = 'cardb.t_driver'
    sql = "select from_city, to_city, priority from %s where phone='%s' limit 1"%(table, phone)
    obj = self.db.get(sql)

    # update driver route and status
    sql = "update %s set status=%s, from_city='%s', to_city='%s'\
        where phone='%s'"%(table, DriverStatus.online, obj.to_city, obj.from_city, phone)
    self.db.execute(sql)

    # put driver to backward route set
    path_rpq = options.driver_rpq + '-'.join([obj.to_city, obj.from_city])
    self.r.zadd(path_rpq, phone, obj.priority)

    # push share message, transfer to offline crontab, accelebrate qps
    # return result
    self.write({'status_code':200, 'error_msg':'', 'is_new':False, 'poolorder_id':poid})


# /cancel_poolorder
class CancelPoolOrderHandler(BaseHandler):
  #def get(self):
  def post(self):
    phone = self.get_argument('phone')
    poid = self.get_argument('poolorder_id')
    super_token = self.get_argument('super_token')
    
    if super_token != options.super_token:
      self.write({'status_code':201, error_msg:'Permission denied!'})
      return
    self.cancel(phone, poid)
  
  def cancel(self, driver_phone, poid):
    table = 'cardb.t_poolorder'

    sql = "update %s set status=%s where id=%s"%(table, POStatus.cancel, poid)
    self.db.execute(sql)

    sql = "select orders from %s where id=%s limit 1"%(table, poid)
    obj = self.db.get(sql)

    # select all sub-orders
    orderids = obj.orders.split(',')
    table = 'cardb.t_order'
    sqls = ["select id, order_type, phone, from_city, to_city, from_place, to_place, \
          num, price, from_lat, from_lng, to_lat, to_lng, dt \
          from %s where id=%s"%(table, oid) for oid in orderids ]

    sql = " union all ".join(sqls) if len(orderids) > 1 else sqls[0]
    objlist = self.db.query(sql)

    # put back all sub-orders
    for obj in objlist:
      path = Path()
      path.from_city = obj.from_city
      path.from_place = obj.from_place
      path.to_city = obj.to_city
      path.to_place = obj.to_place
      path.from_lat = obj.from_lat
      path.from_lng = obj.from_lng
      path.to_lat = obj.to_lat
      path.to_lng = obj.to_lng

      order = Order()
      order.id = obj.id
      order.path = path
      order.phone = obj.phone
      order.number = obj.num
      order.cartype = obj.order_type

      dt_str = obj.dt.strftime("%Y-%m-%d %H:%M:%S")
      dt_arr = time.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
      order.time = (time.mktime(dt_arr) + 3600*8)

      thrift_obj = serialize(order)
      
      pipe = self.r.pipeline()
      pipe.hset(options.order_rm, oid, thrift_obj)
      pipe.lpush(options.order_rq, oid)
      pipe.execute()

    # push cancelled message to users
    pushmsg = Message()
    pushmsg.template_type = TempType.notify
    pushmsg.push_type = PushType.one
    pushmsg.app_type = AppType.user
    pushmsg.title = 'cancel_poolorder'
    
    for obj in objlist: 
      jdict = { 'title':'cancel_poolorder',
        'driver_phone':driver_phone,
        'order_id':obj.id
        }
      pushmsg.content = json.dumps(jdict)
      pushmsg.target = [obj.phone]
      thrift_obj = serialize(pushmsg)
      self.r.lpush(options.queue, thrift_obj)

    # put back driver to redis route set
    #table = 'cardb.t_driver'
    #sql = "select name, carno, from_city, to_city, priority from %s where phone='%s'"%(table, phone)
    #obj = self.db.get(sql)
    #path_rpq = options.driver_rpq + '-'.join([obj.from_city, obj.to_city])
    #self.r.zadd(path_rpq, phone, obj.priority)

    # return result
    self.write({'status_code':200, 'error_msg':'', 'is_new':False})


# /read_pushed_poolorder
class ReadPushedPoolOrderHandler(BaseHandler):
  @base.authenticated
  #def get(self):
  def post(self):
    poid = self.get_argument('poolorder_id')
    postr = self.r.hget(options.poolorder_rm, poid)
    if postr is None or len(postr) == 0: # failed
      #self.write({'status_code':201, 'error_msg':'already canceled or confirmed'})
      self.write({'status_code':201, 'error_msg':u'该订单已取消或已被其他司机接单了'})
      return

    # get orders from poolorder thrift object
    poolorder = PoolOrder()
    poolorder = deserialize(poolorder, postr)

    # display info
    is_subsidy = poolorder.sstype
    total_price = poolorder.subsidy + sum([order.price for order in poolorder.order_list])
    from_city = poolorder.order_list[0].path.from_city
    to_city = poolorder.order_list[0].path.to_city

    order_type = poolorder.cartype
    start_time = ''
    extra_msg = ''

    # special order
    if order_type == POType.special:
      order_id = poolorder.order_list[0].id
      table = 'cardb.t_order'
      sql = "select start_time, msg from %s where id=%s limit 1"%(table, order_id)
      obj = self.db.get(sql)

      start_time = obj.start_time
      extra_msg = obj.msg

    # return result
    msg = {
        'status_code':200,
        'error_msg':'',
        'poolorder_id': poid,
        'total_price': total_price,
        'from_city': from_city,
        'to_city': to_city,
        'order_type': order_type,
        'start_time': start_time,
        'extra_msg': extra_msg,
        'subsidy': poolorder.subsidy
        }
    self.write(msg)


# /get_driver_data
class GetDriverDataHandler(BaseHandler):
  @base.authenticated
  #def get(self):
  def post(self):
    phone = self.current_user

    date = self.get_argument('date')
    today = time.strptime(date, '%Y%m%d')
    today_str = time.strftime('%Y-%m-%d %H:%M:%S', today)

    table = 'cardb.t_poolorder'
    sql = "select sum(price) as income from %s where phone='%s' and status=%s \
        and last_modify>'%s'"%(table, phone, POStatus.done, today_str)
    obj = self.db.get(sql)

    msg = {'status_code':200, 
        'error_msg':'',
        'income_today': obj.income}
    self.write(msg)
