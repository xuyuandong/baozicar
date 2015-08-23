#coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import json
import time
import random
import tornado.web
import tornado.gen

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.options import define, options
from tornado.log import app_log
from math import *

import base
from base import BaseHandler
from base import TempType, PushType, AppType, OrderType, OrderStatus, OLType
from base import POType, POStatus, CouponStatus, DriverStatus
from base import BaseHandler
from ttypes import Path, Order, Message

define("baidu_direction_url", \
    default='http://api.map.baidu.com/direction/v1?mode=driving&output=json&', help='')
define("baidu_api_key", default='ak=286e2613aa2e671c497b40cdcc5f06e7', help='')

# ========================================
# system

# /
class HomeHandler(BaseHandler):
  @base.access_restricted
  def get(self):
    return self.system()

# /index.html
class IndexHandler(BaseHandler):
  @base.access_restricted
  def get(self):
    self.render("index.html")


# /get_server_time
class GetServerTimeHandler(BaseHandler):
  def post(self):
    timestamp = int(1000 * time.time())
    self.write({'status_code':200, 'error_msg':'', 'server_time':timestamp})


# /get_authcode
class GetAuthCodeHandler(BaseHandler):
  @tornado.web.asynchronous
  @tornado.gen.coroutine
  def get(self):
    phone = self.get_argument("phone")
    authcode = '1234' #str(random.randint(1000, 9999))

    result = '-1'
    try:
      self.r.set(options.authcode_rpf + phone, authcode, ex = 300)
      #response = yield self.sendsms(phone, authcode)
      result = '0'#response.body
    except Exception, e:
      app_log.error('sms exception %s', e)
      #self.write({'status_code':201, 'error_msg':'system exception'})
      self.write({'status_code':201, 'error_msg':u'发送验证码失败'})

    if len(result) > 0 and result[0] == '0':
      self.write({'status_code':200, 'error_msg':''})
    else:
      app_log.info('sms error %s', result)
      #self.write({'status_code':201, 'error_msg':'failed to send sms'})
      self.write({'status_code':201, 'error_msg':u'发送验证码失败'})

    # record sms into mysql
    table = 'cardb.t_sms'
    sql = "insert into %s (phone, content, status) \
        values('%s', '%s', '%s');"%(table, phone, authcode, result)
    self.db.execute(sql)

  def sendsms(self, phone, authcode):
    content = '验证码为%s。'%(authcode)
    bodylist= ['corp_id=7f24003',
        'corp_pwd=f24003',
        'corp_service=10690116yd',
        'mobile=' + phone.encode('gb2312'),
        'msg_content=' + content.encode('gb2312'),
        'corp_msg_id=authcode',
        'ext=8888']
    body = '&'.join(bodylist)

    url = 'http://service2.baiwutong.com:8080/sms_send2.do'
    client = AsyncHTTPClient()
    request = HTTPRequest(url, method='POST', body=body)
    return client.fetch(request)


# /query_path
class QueryPathHandler(BaseHandler):
  #@base.authenticated
  #def get(self):
  def post(self): # TODO: check api
    from_city = self.get_argument('from_city')

    # get all possible from_citys
    if len(from_city) == 0:
      self.get_from_citys()
      return

    # get all possible to_citys
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

  def get_from_citys(self):
    table = 'cardb.t_path'
    sql = "select distinct(from_city) from %s"%(table)
    objlist = self.db.query(sql)
    
    result = [ obj.from_city for obj in objlist ]
    msg = {
        'status_code':200,
        'error_msg':'',
        'from_city_list':result
        }
    self.write(msg)

# /query_price
class QueryPriceHandler(BaseHandler):
  #@base.authenticated
  #def get(self):
  def post(self):
    from_city = self.get_argument('from_city')
    from_place = self.get_argument('from_place')
    from_lat = float(self.get_argument('from_lat'))
    from_lng = float(self.get_argument('from_lng'))
    
    to_city = self.get_argument('to_city')
    to_place = self.get_argument('to_place')
    to_lat = float(self.get_argument('to_lat'))
    to_lng = float(self.get_argument('to_lng'))
    
    person_num = int(self.get_argument('person_num'))
    order_type = int(self.get_argument('order_type'))
    app_log.info('order_type=%s', order_type)

    # get path infomation from redis
    path = options.path_rpf + '-'.join([from_city, to_city])
    path_obj = self.r.hgetall(path)
    if path_obj is None or len(path_obj) < 10:
      #self.write({'status_code':201, 'error_msg':'No information for this path in redis'})
      self.write({'status_code':201, 'error_msg':u'系统中不存在此线路信息'})
      return

    # calculate from and to in city place distance
    src_lat = float(path_obj['from_lat'])
    src_lng = float(path_obj['from_lng'])
    src_scale = float(path_obj['from_scale'])
    from_dist = src_scale * self.calc_distance(from_lat, from_lng, src_lat, src_lng)

    dst_lat = float(path_obj['to_lat'])
    dst_lng = float(path_obj['to_lng'])
    dst_scale = float(path_obj['to_scale'])
    to_dist = dst_scale * self.calc_distance(to_lat, to_lng, dst_lat, dst_lng)

    # mileage
    mid_dist = self.calc_distance(src_lat, src_lng, dst_lat, dst_lng)
    mileage = from_dist + mid_dist + to_dist

    # calculate price
    hour = 'h%s'%(time.localtime().tm_hour)
    hour_price = float(path_obj.get(hour, 0))
   
    # from - to city price
    from_step = path_obj['from_pc_step'] if order_type == OrderType.carpool \
        else path_obj['from_bc_step'] 
    to_step = path_obj['to_pc_step'] if order_type == OrderType.carpool \
        else path_obj['to_bc_step'] 

    from_price = max( 0, \
        (from_dist - float(path_obj['from_discount'])) * float(from_step) )
    to_price = max(0, \
        (to_dist - float(path_obj['to_discount'])) * float(to_step) )

    # between city price
    path_price = float(path_obj['pc_price']) * person_num if order_type == OrderType.carpool \
        else float(path_obj['bc_price'])

    # total price
    total_price = from_price + path_price + to_price + hour_price 
    taxi_price = 4.6 * self.calc_distance(to_lat, to_lng, from_lat, from_lng)

    # inside carpool area
    inside = self.inside_carpool_area(from_city, from_lng, from_lat, to_city, to_lng, to_lat)
    maxmile = float(path_obj['maxmile']) if 'maxmile' in path_obj else 10000

    # result
    msg = {
        'status_code': 200,
        'error_msg': '',
        'price': total_price,
        'from_price': from_price,
        'to_price': to_price,
        'path_price': path_price,
        'hour_price': hour_price,
        'taxi_price': taxi_price,
        'mileage': mileage,
        'maxmile': maxmile,
        'inside_carpool_area': inside
        }
    #app_log.info(msg)
    self.write(msg)

  def inside_carpool_area(self, from_city, from_lng, from_lat, to_city, to_lng, to_lat):
    try:
      src_key = options.poolarea_rpf + from_city
      src_lng, src_lat, src_len = self.r.hmget(src_key, 'lng', 'lat', 'threshold')
      from_len = self.calc_distance(from_lat, from_lng, float(src_lat), float(src_lng))

      dst_key = options.poolarea_rpf + to_city
      dst_lng, dst_lat, dst_len = self.r.hmget(dst_key, 'lng', 'lat', 'threshold')
      to_len = self.calc_distance(to_lat, to_lng, float(dst_lat), float(dst_lng))
    
      if from_len > float(src_len) or to_len > float(dst_len):
        return False
    except Exception, e:
      app_log.error('failed to judge inside carpool area [%s]', e)
    
    return True

  def calc_distance(self, lat1, lng1, lat2, lng2):
    #ll = '%s %s, %s %s'%(lat1, lng1, lat2, lng2)
    lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
    a = lat1 - lat2
    b = lng1 - lng2
    s = 2 * asin( sqrt( pow( sin(a/2), 2) + cos(lat1) * cos(lat2) * pow( sin(b/2), 2) ) )
    #ll = ll + ' => %s'%(s * 6378.137)
    #app_log.info(ll)
    return s * 6378.137


# /get_price_detail
class GetPriceDetailHandler(BaseHandler):
  def post(self):
    from_city = self.get_argument('from_city')
    to_city = self.get_argument('to_city')
    
    # get path infomation from redis
    path = options.path_rpf + '-'.join([from_city, to_city])
    path_obj = self.r.hgetall(path)
    if path_obj is None or len(path_obj) < 15:
      self.write({'status_code':201, 'error_msg':u'系统中不存在此线路信息'})
      return

    msg = {'status_code':200,
        'error_msg':'',
        'start_miles':0,
        'start_price':0,
        'over_price_permile':0
        }
    self.write(msg)


# /feedback
class FeedbackHandler(BaseHandler):
  @base.authenticated
  def post(self):
    phone = self.current_user
    content = self.get_argument('content')

    if len(content) > 1024:
      content = content[0:1024]

    table = 'cardb.t_feedback'
    sql = "insert into %s (phone, content) \
        values('%s', '%s');"%(table, phone, content)
    self.db.execute(sql)

    self.write({'status_code':200, 'error_msg':''})


# /get_newest_version
class GetNewestVersionHandler(BaseHandler):
  #@base.authenticated
  def post(self):
    try:
      app = self.get_argument('app_id')
      platform = self.get_argument('platform')
    except Exception, e:
      app = 0
      platform = 0

    table = 'cardb.t_version'
    sql = "select version, url from %s \
        where app=%s and platform=%s limit 1"%(table, app, platform);
    try:
      obj = self.db.get(sql)
    except Exception, e:
      self.write({'status_code':201, 'error_msg':''})
      return

    msg = {'status_code':200, 'error_msg':'',
        'version':obj.version, 'url':obj.url}
    self.write(msg)


# /feedback
class FeedbackHandler(BaseHandler):
  @base.authenticated
  def post(self):
    phone = self.current_user
    content = self.get_argument('content')

    if len(content) > 1024:
      content = content[0:1024]

    table = 'cardb.t_feedback'
    sql = "insert into %s (phone, content) \
        values('%s', '%s');"%(table, phone, content)
    self.db.execute(sql)

    self.write({'status_code':200, 'error_msg':''})


# /get_newest_version
class GetNewestVersionHandler(BaseHandler):
  #@base.authenticated
  def post(self):
    try:
      app = self.get_argument('app_id')
      platform = self.get_argument('platform')
    except Exception, e:
      app = 0
      platform = 0

    table = 'cardb.t_version'
    sql = "select version, url from %s \
        where app=%s and platform=%s limit 1"%(table, app, platform);
    try:
      obj = self.db.get(sql)
    except Exception, e:
      self.write({'status_code':201, 'error_msg':''})
      return

    msg = {'status_code':200, 'error_msg':'',
        'version':obj.version, 'url':obj.url}
    self.write(msg)
