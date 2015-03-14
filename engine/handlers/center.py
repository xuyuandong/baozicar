#coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import json
import random
import tornado.web
import tornado.gen

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.options import define, options
from base import BaseHandler

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
    #content = '验证码:' + authcode
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
