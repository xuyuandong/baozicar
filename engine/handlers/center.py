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
  # def post(self):
  def get(self):
    self.write("hello, please login, idiot")

# /get_authcode
class GetAuthCodeHandler(BaseHandler):
  @tornado.web.asynchronous
  @tornado.gen.coroutine
  def get(self):
    phone = self.get_argument("phone")
    authcode = str(random.randint(1000, 9999))

    result = '-1'
    try:
      self.r.set(options.authcode_rpf + phone, authcode, ex = 300)
      response = yield self.sendsms(phone, authcode)
      result = response.body
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
    #content='尊敬的用户，您好！感谢您选择包子拼车，包子拼车验证码%s已发送到您手机上，美好城市绿色出行，包子拼车为您导航。'%(authcode)
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
    app_log.info('order_type=%s person_num=%s', order_type, person_num)

    # get path infomation from redis
    path = options.path_rpf + '-'.join([from_city, to_city])
    path_obj = self.r.hgetall(path)
    if path_obj is None or len(path_obj) < 15:
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

    # result
    msg = {
        'status_code': 200,
        'error_msg': '',
        'price': total_price,
        'from_price': from_price,
        'to_price': to_price,
        'path_price': path_price,
        'hour_price': hour_price,
        'taxi_price': taxi_price
        }
    app_log.info(msg)
    self.write(msg)

  def calc_distance(self, lat1, lng1, lat2, lng2):
    lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
    a = lat1 - lat2
    b = lng1 - lng2
    s = 2 * asin( sqrt( pow( sin(a/2), 2) + cos(lat1) * cos(lat2) * pow( sin(b/2), 2) ) )
    return s * 6378.137


# /query_price2
class QueryPriceHandler2(BaseHandler):
  #@base.authenticated
  @tornado.web.asynchronous
  @tornado.gen.coroutine
  def post(self):
    from_city = self.get_argument('from_city')
    from_place = self.get_argument('from_place')
    to_city = self.get_argument('to_city')
    to_place = self.get_argument('to_place')
    person_num = self.get_argument('person_num')

    # city 2 city price
    path = options.path_rpf + '-'.join([from_city, to_city])
    path_obj = self.r.hgetall(path)
    if path_obj is None:
      self.write({'status_code':201, 'error_msg':'no price for this path in redis'})
      return

    # from city local price
    from_params = ['origin=%s'%(from_place),
        'destination=%s'%(from_city),
        'origin_region=%s'%(from_city),
        'destination_region=%s'%(from_city)]
    from_response = yield self.direction_api(from_params)
    from_result = self.parse_json(from_response.body)
    if len(from_result) == 0:
      self.write({'status_code':201, 'error_msg':'no result for from_place when querying baidu map'})
      return

    # to city local price
    to_params = ['origin=%s'%(to_place),
        'destination=%s'%(to_city),
        'origin_region=%s'%(to_city),
        'destination_region=%s'%(to_city)]
    to_response = yield self.direction_api(to_params)
    to_result = self.parse_json(to_response.body)
    if len(to_result) == 0:
      self.write({'status_code':201, 'error_msg':'no result for to_place when querying baidu map'})
      return

    # calculate total price
    hour = time.localtime().tm_hour
    from_price = from_result['baidu_price']
    to_price = to_result['baidu_price']
    price = path_obj['price'] * int(person_num) + from_price + to_price

    msg = {
        'status_code': 200,
        'error_msg': '',
        'price': price,
        'from_price': from_result,
        'to_price': to_result,
        'path_price': int(path_value)
        }
    self.write(msg)

  def parse_json(self, json_str):
    try:
      jdict = json.loads(json_str)
      if jdict['status'] != 0 or jdict['type'] != 2:
        app_log.info('json status = %s, type = %s', jdict['status'], jdict['type'])
        return {}
      
      taxi = jdict['result']['taxi']
      result = {
            'distance': int(taxi['distance']),
            'duration': int(taxi['duration']),
            'baidu_price': int(taxi['detail'][0]['total_price'])
          }
      return result

    except Exception, e:
      app_log.info('%s', e)
      return {}

  def direction_api(self, params):
    params.append(options.baidu_api_key)
    url = options.baidu_direction_url + '&'.join(params)

    client = AsyncHTTPClient()
    return client.fetch(url)


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
