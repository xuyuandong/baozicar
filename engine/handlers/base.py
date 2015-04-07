#coding=utf-8

import time, datetime, random, uuid
import functools
import redis

from tornado.options import define, options
from tornado.log import app_log
import tornado.web

define("token_key", default="token", help="token parameter name")
define("device_key", default="dev_id", help="device id parameter name")
define("super_token", default="showmeng1234", help="super manager token")

define('authcode_rpf', default='auth_', help="redis authcode key prefix as map")
define('login_rpf', default='login_', help="redis login user profile key prefix as map")
define('path_rpf', default='path_', help='redis map for path information')

define('order_rq', default='l_order', help='redis order list for scheduler input')
define('order_rm', default='h_order', help='redis order map for scheduler input')
define('lock_rm', default='h_lock', help='redis count map used as order mutex lock')
define('poolorder_rm', default='h_carpool', help='redis poolorder map for scheduler output')
define('driver_rpq', default='z_driver_', help='redis zset for drivers')
define('queue', default='l_message', help='redis queue for push message')

################# coding comment ####################################
# status_code: 200 OK 201 Failed
# order_type: 0 carpool 1 specialcar
# order_status: 0 wait 1 confirm 2 toeval 3 done 4 cancel
# order_list_type: 0 booked 1 toeval 2 done 3 all
# coupon_status: 0 normal 1 expired
# driver status:  0 online 1 offline 2 other
# poolorder_type: 0 carpool 1 specialcar 2 all
# poolorder_status: 0 wait 1 confirm 2 ongoing 3 done 4 cancel
#####################################################################

def enum(**enums):
  return type('Enum', (), enums)

LoginType = enum(user=0, driver=1)

TempType = enum(trans=0, notify=1, link=2)
PushType = enum(app=0, many=1, one=2)
AppType = enum(user=0, driver=1)

OrderType = enum(carpool=0, special=1)
OrderStatus = enum(notpay=-1, wait=0, confirm=1, toeval=2, done=3, cancel=4, discard=5)
OLType = enum(booked=0, toeval=1, done=2, all=3)

POType = enum(carpool=0, special=1)
POStatus = enum(wait=0, confirm=1, unfreeze=2, ongoing=3, done=4, cancel=5)

CouponStatus = enum(normal=0, expired=1, used=2, locked=3)
DriverStatus = enum(online=0, offline=1, busy=2)


class BaseHandler(tornado.web.RequestHandler):

  def set_secure_cookie(self, key, value):
    return self.create_signed_value(key, value, version=1)

  def get_current_user(self):
    try:
      value = self.get_argument(options.token_key)
      devid = self.get_argument(options.device_key)
      uid = self.get_secure_cookie(options.token_key, value, min_version=1)
      
      rkey = options.login_rpf + uid
      return uid if devid == self.r.hget(rkey, 'device') else None
    
    except Exception, e:
      app_log.error("authenticated exception: %s", e)
      return None

  def write_error(self, status_code, **kwargs):
    self.write({"error": status_code})

  @property
  def db(self):
    return self.application.db

  @property
  def paylog(self):
    return self.application.log.paylog

  @property
  def push(self):
    return self.application.push

  @property
  def r(self):
    return redis.Redis(connection_pool = self.application.redis)

  @property
  def alipay_public_key(self):
    return self.application.alipay_public_key

def authenticated(method):
  """Decorate methods that requires the user be logged in."""
  @functools.wraps(method)
  def wrapper(self, *args, **kwargs):
    if not self.current_user:
      self.write({'status_code':404, 'error_msg':'not login'})
      return
    return method(self, *args, **kwargs)
  return wrapper

def access_restricted(method):
  """Decorate methods that access ip restricted."""
  @functools.wraps(method)
  def wrapper(self, *args, **kwargs):
    app_log.info("http access %s", self.request.remote_ip)
    return method(self, *args, **kwargs)
  return wrapper

def uuid(phone):
  t = datetime.datetime.now()
  y = t.year%10
  d = t.day + 31*t.month
  s = t.hour*3600 + t.minute*60 + t.second
  r = phone[-4:]
  ret = '%s%03s%05s%06s%04s'%(y,d,s, t.microsecond, r)
  return int(ret.replace(' ', '0'))

def UUID():
  return str(uuid.uuid1())

def UTC2CST(dt):
    dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    dt_arr = time.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    local_arr = time.localtime(time.mktime(dt_arr) + 3600*8)
    local_str = time.strftime("%Y-%m-%d %H:%M:%S", local_arr)
    return local_str
