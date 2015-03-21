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

import base
from base import BaseHandler

define("baidu_direction_url", \
    default='http://api.map.baidu.com/direction/v1?mode=driving&output=json&', help='')
define("baidu_api_key", default='ak=286e2613aa2e671c497b40cdcc5f06e7', help='')


# ========================================
# system

# /
class HomeHandler(BaseHandler):
  def get(self):
    self.write("hello, please login, idiot")

# /get_authcode
class GetAuthCodeHandler(BaseHandler):
  @tornado.web.asynchronous
  @tornado.gen.coroutine
  def get(self):
    phone = self.get_argument("phone")
    authcode = str(random.randint(1000, 9999))

    result = ''
    try:
      self.r.set('auth_' + phone, authcode, ex = 300)
      response = yield self.sendsms(phone, authcode)
      result = response.body
    except Exception, e:
      print 'exception', e
      self.write({'status_code':201, 'error_msg':'system exception'})

    if len(result) > 0 and result[0] == '0':
      print 'result', result
      self.write({'status_code':200, 'error_msg':''})
    else:
      print 'error', result
      self.write({'status_code':201, 'error_msg':'failed to send sms'})


  def sendsms(self, phone, authcode):
    content='尊敬的用户，您好！感谢您选择包子拼车，包子拼车验证码%s已发送到您手机上，美好城市绿色出行，包子拼车为您导航。'%(authcode)
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
  @tornado.web.asynchronous
  @tornado.gen.coroutine
  def post(self):
    from_city = self.get_argument('from_city')
    from_place = self.get_argument('from_place')
    to_city = self.get_argument('to_city')
    to_place = self.get_argument('to_place')
    person_num = self.get_argument('person_num')

    # city 2 city price
    path = '-'.join([from_city, to_city])
    path_value = '1' # TODO: self.r.hget(options.price_rm, path)
    if path_value is None:
      self.write({'status_code':201, 'error_msg':'no price for this path in redis'})
      return

    # from city local price
    from_params = ['origin=%s'%(from_place),
        'destination=%s'%(from_city),
        'origin_region=%s'%(from_city),
        'destination_region=%s'%(from_city)]
    from_response = yield self.direction_api(from_params)
    from_price = self.parse_json(from_response.body)
    if from_price < 0:
      self.write({'status_code':201, 'error_msg':'no result for from_place when querying baidu map'})
      return

    # to city local price
    to_params = ['origin=%s'%(to_place),
        'destination=%s'%(to_city),
        'origin_region=%s'%(to_city),
        'destination_region=%s'%(to_city)]
    to_response = yield self.direction_api(to_params)
    to_price = self.parse_json(to_response.body)
    if to_price < 0:
      self.write({'status_code':201, 'error_msg':'no result for to_place when querying baidu map'})
      return

    # total price
    hour = time.localtime().tm_hour
    price = int(path_value) * int(person_num) + from_price + to_price

    msg = {
        'status_code': 200,
        'error_msg': '',
        'price': price
        }
    self.write(msg)

  def parse_json(self, json_str):
    try:
      jdict = json.loads(json_str)
      if jdict['status'] != 0 or jdict['type'] != 2:
        app_log.info('json status = %s, type = %s', jdict['status'], jdict['type'])
        return -1
      taxi = jdict['result']['taxi'] 
      distance = int(taxi['distance'])
      baidu_price = int(taxi['detail'][0]['total_price'])
      return baidu_price
    except Exception, e:
      app_log.info('%s', e)
      return -1

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

    table = 'cardb.t_feedback'
    sql = "insert into %s (phone, content) \
        values('%s', '%s');"%(table, phone, content)
    self.db.execute(sql)

    self.write({'status_code':200, 'error_msg':''})
