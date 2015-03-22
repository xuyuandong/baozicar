#coding=utf-8

import time,datetime
import tornado.web
import tornado.gen
import json
import base
import order_util

from tornado.concurrent import run_on_executor
from tornado.options import define, options
from futures import ThreadPoolExecutor
from thrift.TSerialization import *

###################### coding comment ########################
# status_code: 200 OK 201 Failed
# driver status:  0 online 1 offline 2 other
# poolorder_type: 0 carpool 1 specialcar 2 all
# poolorder_status: 0 wait 1 confirm 2 ongoing 3 done 4 cancel
##############################################################
from base import TempType, PushType, AppType, OrderType, OrderStatus, OLType
from base import POType, POStatus, CouponStatus, DriverStatus
from base import BaseHandler
from ttypes import Path, Order, PoolOrder, Message


# /login_driver
class DriverLoginHandler(BaseHandler):
  executor = ThreadPoolExecutor(4)

  @tornado.web.asynchronous
  @tornado.gen.coroutine
  def post(self):
    phone = self.get_argument('phone')
    authcode = self.get_argument('authcode')
    dev_id = self.get_argument('dev_id')
    push_id = self.get_argument('push_id')

    # check authcode
    if authcode != self.r.get(options.authcode_rpf + phone):
      self.write({"status_code":201, "error_msg":"auth code error"})
      return

    # async bind push_id
    if not ( yield self.async_bind(phone, push_id) ):
      self.write({"status_code":201, "error_msg":"bind push_id error"})
      return

    # unique (phone - device) (device - pushid) mapping
    rkey = options.driver_rpf + phone
    pipe = self.r.pipeline(transaction=False)
    pipe.hset(rkey, 'device', dev_id)
    pipe.hset(rkey, 'push', push_id)
    pipe.execute()

    # return token
    token = self.set_secure_cookie(options.token_key, phone)
    self.write({'status_code':200, 'error_msg':'', 'token':token})

  @run_on_executor
  def async_bind(self, phone, push_id):
    ret1 = self.push.user.unbindAliasAll(phone)
    #if ret1['result'].upper() != 'OK':
    #  return False
    ret2 = self.push.user.bindAlias(phone, push_id)
    return (ret2['result'].upper() == 'OK')


# =============================================

# /change_driver_status
class DriverChangeStatusHandler(BaseHandler):
  @base.authenticated
  def post(self):
    phone = self.current_user
    status = self.get_argument('status')

    # update mysql driver status
    table = 'cardb.t_driver'
    sql = "update %s set status=%s where phone='%s'"%(table, status, phone)
    self.db.execute(sql)

    # get driver route
    sql = "select from_city, to_city, priority from %s where phone='%s'"\
        %(table, phone)
    route = self.db.get(sql)

    # update redis scheduler
    path_rpq = options.driver_rpq + '-'.join([route.from_city, route.to_city])
    result = 0
    if int(status) == DriverStatus.offline: # online -> offline
      result = self.r.zrem(path_rpq, phone)
    else:  # offline -> online
      result = self.r.zadd(path_rpq, route.priority, phone)

    # return result
    if result == 1:
      self.write({'status_code':200, 'error_msg':''})
    else:
      self.write({'status_code':201, 'error_msg':'failed to change status'})


# /change_driver_route
class DriverChangeRouteHandler(BaseHandler):
  @base.authenticated
  def post(self):
    phone = self.current_user
    from_city = self.get_argument('from_city')
    to_city = self.get_argument('to_city')

    # select priority
    table = 'cardb.t_driver'
    sql = "select priority from %s where phone='%s'"%(table, phone)
    obj = self.db.get(sql)

    # update mysql
    sql = "update %s set from_city='%s', to_city='%s' where phone='%s'"\
        %(table, from_city, to_city, phone)
    self.db.execute(sql)

    # update redis
    old_path_rpq = options.driver_rpq + '-'.join([to_city, from_city])
    path_rpq = options.driver_rpq + '-'.join([from_city, to_city])

    pipe = self.r.pipeline()
    pipe.zrem(old_path_rpq, phone)
    pipe.zadd(path_rpq, obj.priority, phone)
    pipe.execute()

    # return result
    self.write({'status':200, 'error_msg':''})



# /get_poolorder_list
class GetPoolOrderListHandler(BaseHandler):
  @base.authenticated
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

    sql = "select po_id, po_type, status, from_city, to_city, price, dt\
        from %s where phone='%s' %s"%(table, phone, condition)
    objlist = self.db.query(sql)

    # poolorder list
    polist = [{
       'poolorder_id': obj.po_id,
       'poolorder_date': obj.dt.strftime("%Y-%m-%d %H:%M:%S"),
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
        'poolorder_count':1,
        'poolorder_infos': polist
        }
    self.write(msg)


# /get_poolorder_detail
class GetPoolOrderDetailHandler(BaseHandler):
  @base.authenticated
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
        from %s where po_id='%s'"%(table, poid)
    obj = self.db.get(sql)

    # select user info from sub-orders
    table = 'cardb.t_order'
    if curday < dstday:
      table = table + "_" + date
    orderids = obj.orders.split(',')

    sqls = [ "select phone, name, from_place, to_place, start_time, msg\
          from %s where id=%s"%(table, oid) for oid in orderids ]
    sql = " union all ".join(sqls) if len(orderids) > 1 else sqls[0]

    orders = self.db.query(sql)
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
  def post(self):
    phone = self.current_user
    status = self.get_argument('status')

    # confirm->32bit string id, else->integer id
    poid = self.get_argument('poolorder_id')

    action = {
        POStatus.confirm: self.confirm,
        POStatus.unfreeze: self.unfreeze,
        POStatus.ongoing: self.ongoing,
        POStatus.done: self.done,
        POStatus.cancel: self.cancel
        }
    # switch status to pick method
    if int(status) in action:
      action.get(int(status))(phone, poid)
    else:
      self.write({'status_code':201, 'error_msg':'wrong action status'})


  def confirm(self, phone, poid):
    # get poolorder
    postr = self.r.hget(options.poolorder_rm, poid)
    if len(postr) == 0: # failed
      self.write({'status_code':201, 'error_msg':'already canceled or confirmed'})
      return

    # get orders from poolorder thrift object
    poolorder = PoolOrder()
    poolorder = deserialize(poolorder, postr)

    orderids = [ str(order.id) for order in poolorder.order_list ]
    userphones = [order.phone for order in poolorder.order_list ]
    total_price = sum([order.price for order in poolorder.order_list])

    # try confirm
    ret = order_util.ConfirmOrder(self.r, orderids)

    if ret is True: # success
      # from & to city
      from_city = poolorder.order_list[0].path.from_city
      to_city = poolorder.order_list[0].path.to_city

      # weather to remove driver from sheduler queue
      status = POStatus.confirm
      if poolorder.cartype == POType.carpool:
        status = POStatus.ongoing
        path_rpq = options.driver_rpq + '-'.join([from_city, to_city])
        self.r.zrem(path_rpq, phone)

      # insert poolorder into mysql
      table = 'cardb.t_poolorder'
      sql = "insert into %s \
          (po_id, po_type, status, price, phone, from_city, to_city, orders, dt) \
          values('%s', %s, %s, %s, '%s', '%s', '%s', '%s', null)"\
          %(table, poid, poolorder.cartype, status,
          total_price, phone, from_city, to_city, ','.join(orderids))
      self.db.execute(sql)

      # coupon unique id generator
      obj = self.db.get("select last_insert_id() as id")
      poolorder_id = obj.id

      # push message
      pushmsg = Message()
      pushmsg.template_type = TempType.trans
      pushmsg.push_type = PushType.many
      pushmsg.app_type = AppType.user
      pushmsg.title = 'poolorder'
      pushmsg.content = phone  # driver info
      pushmsg.target = userphones
      thrift_obj = serialize(pushmsg)
      self.r.lpush(options.queue, thrift_obj)

      # return result
      self.write({'status_code':200, 'error_msg':'', 'poolorder_id':poolorder_id})
    else:
      self.write({'status_code':201, 'error_msg':'already canceled or confirmed'})


  def unfreeze(self, phone, poid):
    table = 'cardb.t_poolorder'
    sql = "select from_city, to_city from %s where id=%s"%(table, poid)
    obj = self.db.get(sql)

    path_rpq1 = options.driver_rpq + '-'.join([obj.from_city, obj.to_city])
    path_rpq2 = options.driver_rpq + '-'.join([obj.to_city, obj.from_city])

    pipe = self.r.pipeline(transaction=False)
    ret = pipe.zrem(path_rpq1, phone).zrem(path_rpq2, phone).execute()

    if ret[0] + ret[1] > 0:
      self.write({'status_code':200, 'error_msg':''})
    else:
      self.write({'status_code':201, 'error_msg':'failed to unfreeze, driver is not available'})


  def ongoing(self, phone, poid):
    table = 'cardb.t_poolorder'
    sql = "update %s set status=%s where id=%s"%(table, POStatus.ongoing, poid)
    self.db.execute(sql)

    self.write({'status_code':200, 'error_msg':''})


  def done(self, phone, poid):
    # update poolorder status
    table = 'cardb.t_poolorder'
    sql = "update %s set status=%s where id=%s"%(table, POStatus.done, poid)
    self.db.execute(sql)

    # select orders from poolorder
    sql = "select orders from %s where id=%s"%(table, poid)
    obj = self.db.get(sql)
    orderids = obj.orders.split(',')

    # update order status
    table = 'cardb.t_order'
    order_condition = ','.join([str(oid) for oid in orderids])
    sql = "update %s set status=%s where id in (%s)"%(table, OrderStatus.done, order_condition)
    self.db.execute(sql)

    # select driver route and priority
    table = 'cardb.t_driver'
    sql = "select from_city, to_city, priority from %s where phone='%s'"%(table, phone)
    obj = self.db.get(sql)

    # update driver route and status
    sql = "update %s set status=%s, from_city='%s', to_city='%s'\
        where phone='%s'"%(table, DriverStatus.online, obj.to_city, obj.from_city, phone)
    self.db.execute(sql)

    # put driver to backward route set
    path_rpq = options.driver_rpq + '-'.join([obj.to_city, obj.from_city])
    self.r.zadd(path_rpq, obj.priority, phone)

    # push share message, transfer to offline crontab, accelebrate qps
    # return result
    self.write({'status_code':200, 'error_msg':''})


  def cancel(self, phone, poid):
    table = 'cardb.t_poolorder'

    sql = "update %s set status=%s where id=%s"%(table, POStatus.cancel, poid)
    self.db.execute(sql)

    sql = "select orders from %s where id=%s"%(table, poid)
    obj = self.db.get(sql)

    # select all sub-orders
    orderids = obj.orders.split(',')
    table = 'cardb.t_order'
    sqls = ["select id, order_type, phone, from_city, to_city, from_place, to_place, num, price\
          from %s where id=%s"%(table, oid) for oid in orderids ]

    sql = " union all ".join(sqls) if len(orderids) > 1 else sqls[0]
    objlist = self.db.query(sql)

    # put back all sub-orders
    userphones = []
    for obj in objlist:
      userphones.append(obj.phone)

      path = Path()
      path.from_city = obj.from_city
      path.to_city = obj.to_city
      path.from_place = obj.from_place
      path.to_place = obj.to_place

      order = Order()
      order.id = obj.id
      order.path = path
      order.phone = obj.phone
      order.number = obj.num
      order.cartype = obj.order_type

      thrift_obj = serialize(order)
      pipe = self.r.pipeline()
      pipe.hset(options.order_rm, oid, thrift_obj)
      pipe.lpush(options.order_rq, oid)
      pipe.execute()

    # put back driver to redis route set
    table = 'cardb.t_driver'
    sql = "select from_city, to_city, priority from %s where phone='%s'"%(table, phone)
    obj = self.db.get(sql)

    path_rpq = options.driver_rpq + '-'.join([obj.from_city, obj.to_city])
    self.r.zadd(path_rpq, obj.priority, phone)

    # push message
    pushmsg = Message()
    pushmsg.template_type = TempType.trans
    pushmsg.push_type = PushType.many
    pushmsg.app_type = AppType.user
    pushmsg.title = 'poolorder'
    pushmsg.content = 'cancel old, wait for new driver to confirm'
    pushmsg.target = userphones
    thrift_obj = serialize(pushmsg)
    self.r.lpush(options.queue, thrift_obj)

    # return result
    self.write({'status_code':200, 'error_msg':''})


# /read_pushed_poolorder
class ReadPushedPoolOrder(BaseHandler):
  @base.authenticated
  def post(self):
    poid = self.get_argument('poolorder_id')
    postr = self.r.hget(options.poolorder_rm, poid)
    if len(postr) == 0: # failed
      self.write({'status_code':201, 'error_msg':'already canceled or confirmed'})
      return

    # get orders from poolorder thrift object
    poolorder = PoolOrder()
    poolorder = deserialize(poolorder, postr)

    # display info
    total_price = sum([order.price for order in poolorder.order_list])
    from_city = poolorder.order_list[0].path.from_city
    to_city = poolorder.order_list[0].path.to_city

    order_type = poolorder.cartype
    start_time = ''
    extra_msg = ''

    # special order
    if order_type == POType.special:
      order_id = poolorder.order_list[0].id
      table = 'cardb.t_order'
      sql = "select start_time, msg from %s where id=%s"%(table, order_id)
      obj = self.db.get(sql)

      start_time = obj.start_time
      extra_msg = obj.msg

    # return result
    msg = {
        'status_code':200,
        'error_msg':'',
        'total_price': total_price,
        'from_city': from_city,
        'to_city': to_city,
        'order_type': order_type,
        'start_time': start_time,
        'extra_msg': extra_msg
        }
    self.write(msg)

