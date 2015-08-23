#coding=utf-8
import sys                                      
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import time
import json
import redis
import logging
import urllib
import urllib2

import tornado
from tornado.log import app_log
from tornado.options import define, options
from tornado.httpclient import HTTPClient, HTTPRequest

from thrift.TSerialization import * 
from genpy.scheduler.ttypes import *

from dbutil import DBUtil


####################################################################
# ttype: template type, 0: Transmission, 1: Notification, 2: Link
# ptype: push type, 0: App, 1: List, 2: Single
def enum(**enums):
  return type('Enum', (), enums)
TempType = enum(trans=0, notify=1, link=2)
PushType = enum(app=0, many=1, one=2)
AppType = enum(user=0, driver=1)
OrderType = enum(carpool=0, special=1, booking=2)


####################################################################

class Translator(object):
  def __init__(self, pc):
    self.pc = pc
    self.db = pc.db
  
  # /poolorder
  def PoolOrder(self, tobj):
    d = {'ttype': [TempType.trans, TempType.notify],
         'ptype': tobj.push_type,
         'title': u'包子拼车新订单信息', #tobj.title,
         'text':  u'有新的订单来了，赶快来抢吧', #tobj.text,
         'url':   tobj.url,
         'target':tobj.target,
         'APPID': self.pc.appId[tobj.app_type],
         'APPKEY':self.pc.appKey[tobj.app_type]
        }
    try:
      po = PoolOrder()
      po = deserialize(po, tobj.content)
      d['content'] = json.dumps( {'title':'poolorder', 'poolorder_id':po.id} ) 
    except Exception, e:
      app_log.error("deserialize thrift error, ", e)
    return d

  # /confirm_poolorder
  def ConfirmPoolOrder(self, tobj):
    # sms message
    jdict = json.loads(tobj.content)
    order_type = jdict['order_type']
    app_log.info('order type = %s', order_type)
    if order_type != OrderType.booking:
      self.__confirm_poolorder_normal(jdict, tobj.target)
    else:
      self.__confirm_poolorder_booking(jdict, tobj.target)

    # getui message
    d = {'ttype': [TempType.trans, TempType.notify],
         'ptype': tobj.push_type,
         'title': u'包子拼车推送信息', #tobj.title,
         'text':  u'您的订单已有司机接单啦，赶紧查看吧', #tobj.text,
         'content': tobj.content,
         'url':   tobj.url,
         'target':tobj.target,
         'APPID': self.pc.appId[tobj.app_type],
         'APPKEY':self.pc.appKey[tobj.app_type]
        }
    return d
  
  def __confirm_poolorder_normal(self, jdict, target):
    try:
      driver = jdict['driver_phone']
      order_id = jdict['order_id']
      per_subsidy = jdict['per_subsidy']

      table = 'cardb.t_order'
      sql = "select fact_price from %s where id=%s"%(table, order_id)
      subsidy = per_subsidy - self.db.get(sql).fact_price

      table = 'cardb.t_driver'
      sql = "select name, carno from %s where phone='%s' limit 1"%(table, driver)
      obj = self.db.get(sql)

      content = '''您的订单号为%s的订单已有司机接单，此单包子拼车为您补贴%s元！
      司机 %s，电话%s，车牌号 %s，司机师傅会在3分钟内联系您。
      为保障您的权益，如遇司机拒单爽约，让您转乘其他车辆，加收费用，不上门接送等现象，请致电：4008-350-650'''\
          %(order_id, int(subsidy), obj.name, driver, obj.carno)

      response = SendSms2(target, content)
      app_log.info('confirm sms ret: %s', response)#.body)
    except Exception, e:
      app_log.info('confirm sms error: %s %s', e, target)

  def __confirm_poolorder_booking(self, jdict, target):
    pass

  # /cancel_booking_poolorder
  def CancelBookingPoolOrder(self, tobj):
    # TODO: maybe use sms
    d = {'ttype': [TempType.trans, TempType.notify],
         'ptype': tobj.push_type,
         'title': u'包子拼车推送信息', #tobj.title,
         'text':  u'乘客取消了预约订单，请查看详情', #tobj.text,
         'content': tobj.content,
         'url':   tobj.url,
         'target':tobj.target,
         'APPID': self.pc.appId[tobj.app_type],
         'APPKEY':self.pc.appKey[tobj.app_type]
        }
    return d

  # /booking_deal
  def BookingDeal(self, tobj):
    d = {'ttype': [TempType.trans, TempType.notify],
         'ptype': tobj.push_type,
         'title': u'包子拼车推送信息', #tobj.title,
         'text':  u'乘客确认并支付了预约订单，请查看详情', #tobj.text,
         'content': tobj.content,
         'url':   tobj.url,
         'target':tobj.target,
         'APPID': self.pc.appId[tobj.app_type],
         'APPKEY':self.pc.appKey[tobj.app_type]
        }
    return d

  # /system_notify
  def SystemNotify(self, tobj):
    pass


########################################################################
def SendSms(target, content):
  phone = ','.join(target)
  bodylist= ['corp_id=7f24003',
        'corp_pwd=f24003',
        'corp_service=10690116yd',
        'mobile=' + phone.encode('gb2312'),
        'msg_content=' + content.encode('gb2312'),
        'corp_msg_id=confirm_order',
        'ext=8888']
  body = '&'.join(bodylist)
  #app_log.info('sms body: %s', body)
  url = 'http://service2.baiwutong.com:8080/sms_send2.do'
  client = HTTPClient()
  request = HTTPRequest(url, method='POST', body=body)
  return client.fetch(request)

def SendSms2(target, content):
  phone = ','.join(target)
  bodylist= {
        'corp_id':'7f24003',
        'corp_pwd':'f24003',
        'corp_service':'10690116yd',
        'mobile' : phone.encode('gb2312'),
        'msg_content' : content.encode('gb2312'),
        'corp_msg_id':'confirm_order',
        'ext':'8888'
        }

  url = 'http://service2.baiwutong.com:8080/sms_send2.do'
  post_data = urllib.urlencode(bodylist)
  
  request = urllib2.Request(url, post_data)
  response = urllib2.urlopen(request)
  return response.read()
