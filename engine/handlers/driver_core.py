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



# /change_poolorder_status
class ChangePoolOrderStatusHandler(BaseHandler):
  @base.authenticated
  #def get(self):
  def post(self):
    phone = self.current_user
    # confirm->32bit string id, else->integer id
    poid = self.get_argument('poolorder_id')
    status = int(self.get_argument('status'))
    app_log.info('poolorder=%s, status=%s', poid, status)

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
    if not self.__confirm_check_driver(phone):
      self.write({'status_code':201, \
          'temp_poolorder_id': poid, 'is_new':True, \
          'error_msg':u'亲，请先把乘客送到家再来抢单哦'})
          #'error_msg':'driver status is not online'})
      return

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
    original_price = poolorder.subsidy + sum([order.price for order in poolorder.order_list])
    
    # <NOTE> operation demand ###
    person_num = sum([order.number for order in poolorder.order_list])
    feed = self.r.hget(options.path_rpf + path, 'feed')
    total_price = original_price
    if feed is not None:
      total_price = int(feed) * person_num + original_price

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
    status = POStatus.confirm if (poolorder.cartype >= POType.special) else POStatus.ongoing
    self.__confirm_update_driver_status(phone, priority, path, status)

    # insert poolorder into mysql
    poolorder_id = base.uuid(phone)

    table = 'cardb.t_poolorder'
    sql = "insert into %s \
        (id, po_id, po_type, status, price, phone, from_city, to_city, orders, \
        subsidy, sstype, dt, original_price) \
        values(%s, '%s', %s, %s, %s, '%s', '%s', '%s', '%s', %s, %s, null, %s)"\
        %(table, poolorder_id, poid, poolorder.cartype, status,
        total_price, phone, from_city, to_city, ','.join(orderids),
        poolorder.subsidy, poolorder.sstype, original_price)
    self.db.execute(sql)

    # update orders status
    self.__confirm_update_order_status(phone, poolorder, poolorder_id)

    # push response message to users
    per_subsidy = total_price / person_num
    self.__confirm_push_message(phone, poolorder, per_subsidy)

    # return result
    self.write({'status_code':200, 'is_new':True, 'error_msg':'', \
        'poolorder_id':poolorder_id, 'temp_poolorder_id':poid })

  def __confirm_check_driver(self, phone):
    table = 't_driver'
    sql = "select status from %s where phone='%s' limit 1"%(table, phone)
    status = self.db.get(sql).status
    return (status == DriverStatus.online)

  def __confirm_lock_driver(self, phone, path):
    driver_rpq = options.driver_rpq + path
    priority = self.r.zscore(driver_rpq, phone)
    ret = self.r.zrem(driver_rpq, phone)
    return priority if (ret > 0) else -1

  def __confirm_unlock_driver(self, phone, path, priority):
    driver_rpq = options.driver_rpq + path
    self.r.zadd(driver_rpq, phone, priority)
      

  def __confirm_update_driver_status(self, phone, priority, path, poolorder_status):
    #path_obj = options.path_rpf + path
    #driver_num = self.r.hget(path_obj, 'driver_num')
    #priority = priority + int(driver_num)
    
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

  def __confirm_update_order_status(self, phone, poolorder, poolorder_id):
    order_list = poolorder.order_list

    table = 'cardb.t_order'
    order_condition = ','.join([str(order.id) for order in order_list])
    sql = "update %s set status=%s, driver='%s', poolorder_id=%s \
        where id in (%s)"%(table, OrderStatus.confirm, phone, poolorder_id, order_condition)
    self.db.execute(sql)

  def __confirm_push_message(self, driver_phone, poolorder, per_subsidy):
    pushmsg = Message()
    pushmsg.template_type = TempType.notify
    pushmsg.push_type = PushType.one
    pushmsg.app_type = AppType.user
    pushmsg.title = 'confirm_poolorder'
    
    for order in poolorder.order_list:
      jdict = { 'title': 'confirm_poolorder',
          'driver_phone': driver_phone,
          'order_id': order.id,
          'order_type': poolorder.cartype,
          'per_subsidy': per_subsidy
          }
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
    # get sub-order ids and user phones
    table = 'cardb.t_order'
    sqls = "select id, phone from %s where poolorder_id=%s"%(table, poid)
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
    sql = "select price, status, orders from %s where id=%s limit 1"%(table, poid)
    obj = self.db.get(sql)

    # protect redo multiple times
    if obj.status == POStatus.done:
      self.write({'status_code':200, 'error_msg':'', 'is_new':False, 'poolorder_id':poid})
      return

    # update poolorder status
    sql = "update %s set status=%s where id=%s"%(table, POStatus.done, poid)
    self.db.execute(sql)
    
    # update order status
    table = 'cardb.t_order'
    sql = "update %s set status=%s where poolorder_id=%s"%(table, OrderStatus.toeval, poid)
    self.db.execute(sql)

    # update driver data
    table = 'cardb.t_driver_data'
    sql = "select income, ponum from %s where phone='%s'"%(table, phone)
    all_data = self.db.get(sql)
    if all_data is None:
      sql = "insert into %s (phone, income, ponum, mileage, dt) \
          values('%s', %s, %s, %s, null)"%(table, phone, obj.price, 1, 0)
      self.db.execute(sql)
    else:
      sql = "update %s set income=%s, ponum=%s where phone='%s'"\
          %(table, all_data.income + obj.price, all_data.ponum + 1, phone)
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

    # select all sub-orders
    table = 'cardb.t_order'
    sqls = "select id, order_type, phone, from_city, to_city, from_place, to_place, \
          num, price, from_lat, from_lng, to_lat, to_lng, dt \
          from %s where poolorder_id=%s"%(table, poid)
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
      order.time = (time.mktime(dt_arr))

      thrift_obj = serialize(order)
      
      #pipe = self.r.pipeline()
      #pipe.hset(options.order_rm, oid, thrift_obj)
      #pipe.lpush(options.order_rq, oid)
      #pipe.execute()

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
      #self.r.lpush(options.queue, thrift_obj)

    # put back driver to redis route set
    table = 'cardb.t_driver'
    sql = "update %s set status=%s where phone='%s'"%(table, DriverStatus.online, phone)
    self.db.execute(sql)

    sql = "select name, carno, from_city, to_city, priority from %s where phone='%s'"%(table, phone)
    obj = self.db.get(sql)
    
    path_rpq = options.driver_rpq + '-'.join([obj.from_city, obj.to_city])
    self.r.zadd(path_rpq, phone, obj.priority)

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
    original_price = poolorder.subsidy + sum([order.price for order in poolorder.order_list])
    from_city = poolorder.order_list[0].path.from_city
    to_city = poolorder.order_list[0].path.to_city

    order_type = poolorder.cartype
    start_time = ''
    extra_msg = ''

    station = poolorder.from_station if poolorder.from_station is not None else from_city

    # <NOTE> operation demand ###
    person_num = sum([order.number for order in poolorder.order_list])
    path = '-'.join([from_city, to_city])
    feed = self.r.hget(options.path_rpf + path, 'feed')
    total_price = original_price
    if feed is not None:
      total_price = int(feed) * person_num + original_price

    # special order, booking order
    if order_type >= POType.special:
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
        'subsidy': poolorder.subsidy,
        'station': station,
        'original_price': original_price,
        'person_num': person_num
        }
    self.write(msg)


# /read_cancel_booking_poolorder
class ReadCancelPoolOrderHandler(BaseHandler):
  @base.authenticated
  def post(self):
    pass


# /read_booking_deal
class ReadBookingDeal(BaseHandler):
  @base.authenticated
  def post(self):
    pass
