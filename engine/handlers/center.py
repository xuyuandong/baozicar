#coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import json
import random
import tornado.web
import tornado.gen
import base

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.options import define, options
from base import BaseHandler

define("baidu_direction_url", default='http://api.map.baidu.com/direction/v1?mode=driving&output=json&', help='')
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
    path_value = self.r.hget(options.price_rm, path)
    if len(path_value) == 0:
      self.write({'status_code':201, 'error_msg':'no price for this path'})
      return

    # from city local price
    from_params = ['origin=%s'%(from_place),
        'destination=%s'%(from_city),
        'origin_region=%s'%(from_city),
        'destination_region=%s'%(from_city)]
    from_json = yield self.direction_api(from_params)
    from_price = self.parse_json(from_json)

    # to city local price
    to_params = ['origin=%s'%(to_place),
        'destination=%s'%(to_city),
        'origin_region=%s'%(to_city),
        'destination_region=%s'%(to_city)]
    to_json = yield self.direction_api(to_params)
    to_price = self.parse_json(to_price)

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
    pass

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
