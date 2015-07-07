#coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import time,datetime
import tornado.web
import tornado.gen
import json
import base

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.concurrent import run_on_executor
from tornado.options import define, options
from tornado.log import app_log

from futures import ThreadPoolExecutor

###################### coding comment ########################
# status_code: 200 OK 201 Failed
# driver status:  0 online 1 offline 2 other
# poolorder_type: 0 carpool 1 specialcar 2 all
# poolorder_status: 0 wait 1 confirm 2 ongoing 3 done 4 cancel
##############################################################
from base import LoginType, TempType, PushType, AppType, OrderType, OrderStatus, OLType
from base import POType, POStatus, CouponStatus, DriverStatus
from base import BaseHandler


# /driver_recommend_user
class DriverRecommendUserHandler(BaseHandler):

  @base.authenticated
  @tornado.web.asynchronous
  @tornado.gen.coroutine
  #def get(self):
  def post(self):
    phone = self.current_user
    user = self.get_argument('user')
    if phone == user:
      self.write({'status_code':201, 'error_msg':u'You cannot recommend yourself'})
      return

    table = 'cardb.t_drecuser'    
    sql = "select id from %s where user_phone='%s' limit 1"%(table, user)
    obj = self.db.get(sql)
    if obj is not None:
      #self.write({'status_code':201, 'error_msg':u'The user is already recommended'})
      self.write({'status_code':201, 'error_msg':u'该乘客已经被其他大叔抢先推荐了'})
      return

    date = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
    sql = "select count(1) as num from %s \
        where driver_phone='%s' and dt>'%s'"%(table, phone, date)
    obj = self.db.get(sql)
    if obj.num >= 50:
      #self.write({'status_code':201, 'error_msg':u'Today you already recommend 50 users'})
      self.write({'status_code':201, 'error_msg':u'今天您已经推荐50个乘客了，明天再推'})
      return

    result = '-1'
    try:
      response = yield self.sendsms(phone, user)
      result = response.body
    except Exception, e:
      app_log.info('rec sms exception: %s', e)
      
    if result[0] != '0':
      app_log.info('rec sms failed: %s', result)
      self.write({'status_code':201, 'error_msg':u'您的推荐请求未发送成功，请稍后重试'})
      return

    sql = "insert into %s (driver_phone, user_phone, status, dt) \
        values('%s', '%s', %s, null)"%(table, phone, user, 0)
    self.db.execute(sql)

    self.write({'status_code':200, 'error_msg':''})

  def sendsms(self, driver, user):
    table = 'cardb.t_driver'
    sql = "select name from %s where phone='%s' limit 1"%(table, driver)
    name = self.db.get(sql).name
   
    table = 'cardb.t_version'
    sql = "select url from %s where app=-1 and platform=-1"%(table)
    link = self.db.get(sql).url

    content = '包子大叔推荐您使用包子拼车软件，下载地址：%s 。'%(link)

    bodylist= ['corp_id=7f24003',
        'corp_pwd=f24003',
        'corp_service=10690116yd',
        'mobile=' + user.encode('gb2312'),
        'msg_content=' + content.encode('gb2312'),
        'corp_msg_id=authcode',
        'ext=8888']
    body = '&'.join(bodylist)

    url = 'http://service2.baiwutong.com:8080/sms_send2.do'
    client = AsyncHTTPClient()
    request = HTTPRequest(url, method='POST', body=body)
    return client.fetch(request)

# =============================================

# /wxshare_app
class WxshareAppHandler(BaseHandler):

  @base.authenticated
  def post(self):
    phone = self.current_user
    code = self.get_share_id(phone)
    self.write({'status_code':200, 'error_msg':'', 'code':code})

  @base.authenticated
  def post(self):
    phone = self.current_user
    code = self.get_share_id(phone)
    
    table = 'cardb.t_wxshare_app'
    sql = "select phone from %s where phone='%s' limit 1"%(table, phone)
    obj = self.db.get(sql)

    if obj is None: # first time share
      sql = "insert into %s (phone, code, dt) \
          values('%s', %s, null)"%(table, phone, code)
      self.db.execute(sql)
      self.first_share_reward(phone)

    self.share_coupon(code)
    self.write({'status_code':200, 'error_msg':''})

  def get_share_id(self, phone):
    code = ''
    pos = [2,4,6,8,10,9,7,5,3,1]

    for p in pos:
      code = code + phone[p]

    if len(phone) > 11:
      code = code + phone[11:]
    
    return code

  def first_share_reward(self, phone, code):
    deadline = datetime.datetime.now() + datetime.timedelta(days = 30)
    coupon = {'ctype': -1,
        'price': 5,
        'within': 0,
        'deadline': deadline.strftime('%Y-%m-%d'),
        'note': u'首次分享奖励'}
    coupon_id = base.uuid(phone)

    table = 'cardb.t_coupon'
    sql = "insert into %s (id, ctype, status, price, within, deadline, note, phone, code, dt) \
        values(%s, %s, %s, %s, %s, '%s', '%s', '%s', %s, null)" \
        %(table, coupon_id, coupon['ctype'], CouponStatus.normal, \
        coupon['price'], coupon['within'], coupon['deadline'], coupon['note'], phone, 1)
    self.db.execute(sql)

  def share_coupon(self, exchange_code):
    value = {
        'num': 100,  # how many people can exchange
        'ctype': -1, # car type, 0->carpool, 1->specail car
        'note': '', # decription
        'deadline': '', 
        'duration': 10, # if no deadline, use 'current time + duration days'
        'within': 200, # total price must higher than this
        'price': 1  # coupon price
        }

    rkey = 'c_' + str(exchange_code)
    self.r.hmset(rkey, value)
    self.r.expire(rkey, 30*24*3600)
