# coding=utf-8
import sys                                      
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import time
import json
import redis
import logging

from igetui.template import *
from igetui.template.igt_base_template import *
from igetui.template.igt_transmission_template import *
from igetui.template.igt_link_template import *
from igetui.template.igt_notification_template import *
from igetui.template.igt_notypopload_template import *
from igetui.template.igt_apn_template import *

import tornado
from tornado.log import app_log
from tornado.options import define, options
from push_util import PushUtil 
from thrift.TSerialization import * 

from genpy.scheduler.ttypes import *


define("host", default = "localhost", help = "")
define("port", default = 6379, help = "", type = int)
define("queue", default = "l_message", help = "")

define("log", default = "logs/log.", help = "")
define("pid", default = 0, help = "process id", type = int)

define("USER_APPID", default = "qlZIF87hye8ZzyifZIEMn3", help = "")
define("USER_APPKEY", default = "WqJDqjvFPL9BBZ3NxIsNRA", help = "")
define("USER_APPSECRET", default = "QSfgiPT5YB9W4OrNp24hc5", help = "")
define("USER_MASTERSECRET", default = "FU1XLZGDlH9WA5u4j3nHA7", help = "")

define("SERV_APPID", default = "p35rm5CQNi8ELMOKsXnhqA", help = "")
define("SERV_APPKEY", default = "AbUz7mQ8k199NbT9yv6UB1", help = "")
define("SERV_APPSECRET", default = "HKxtQHnZjc9yqGbH021ET4", help = "")
define("SERV_MASTERSECRET", default = "XCfOSceoiM8lADovc9365A", help = "")

#toList接口每个用户返回用户状态开关,true：打开 false：关闭
os.environ['needDetails'] = 'true'

#数据经SDK传给客户端，由客户端代码觉得如何展现给用户
def GetTransmissionTemplate(dobj):
    template = TransmissionTemplate()
    template.transmissionType = 2
    template.appId = dobj['APPID']
    template.appKey = dobj['APPKEY']
    template.transmissionContent = dobj['content']
    #iOS 推送需要的PushInfo字段 前三项必填，后四项可以填空字符串
    #template.setPushInfo(actionLocKey, badge, message, sound, payload, locKey, locArgs, launchImage)
    #template.setPushInfo("",2,"","","","","","");
    return template

#通知栏显示含图标、标题、内容通知，点击后激活应用, IOS不推荐
def GetNotificationTemplate(dobj):
    template = NotificationTemplate()
    template.appId = dobj['APPID']
    template.appKey = dobj['APPKEY']
    template.transmissionType = 2
    template.title = dobj['title']
    template.text = dobj['text']
    template.transmissionContent = dobj['content']
    template.logo = ""
    template.logoURL = ""
    template.isRing = True
    template.isVibrate = True
    template.isClearable = True
    #iOS 推送需要的PushInfo字段 前三项必填，后四项可以填空字符串
    #template.setPushInfo("open",4,"message","","","","","");
    return template

#通知栏显示含图标、标题、内容通知，点击后打开指定网页，IOS不推荐
def GetLinkTemplate(dobj):
    template = LinkTemplate()
    template.appId = dobj['APPID']
    template.appKey = dobj['APPKEY']
    template.title = dobj['title']
    template.text = dobj['text']
    template.logo = ""
    template.url = dobj['url']
    template.transmissionType = 1
    template.transmissionContent = dobj['content']
    template.isRing = True
    template.isVibrate = True
    template.isClearable = True
    #iOS 推送需要的PushInfo字段 前三项必填，后四项可以填空字符串
    #template.setPushInfo("open",4,"message","test1.wav","","","","");
    return template

####################################################################
# ttype: template type, 0: Transmission, 1: Link, 2: Notification
# ptype: push type, 0: App, 1: List, 2: Single

class PushCenter(object):
  def __init__(self, name, port):
    self.pusher = {
        0: PushUtil(options.USER_APPID, options.USER_APPKEY, options.USER_MASTERSECRET),
        1: PushUtil(options.SERV_APPID, options.SERV_APPKEY, options.SERV_MASTERSECRET)
        }
    self.templateAction = {
        0: GetTransmissionTemplate,
        1: GetLinkTemplate,
        2: GetNotificationTemplate
        }
    self.pushAction = {
        0: lambda p, temp, tar: p.ToApp(temp, tar),
        1: lambda p, temp, tar: p.ToList(temp, tar),
        2: lambda p, temp, tar: p.ToSingle(temp, tar)
        }
    self.translateAction = {
        'poolorder': self.TranslatePoolOrder,
        'confirm_poolorder': self.TranslateConfirmOrder,
        'cancel_poolorder': self.TranslateCancelOrder,
        'system_note': self.TranslateSystemNote
        }
    self.appId = {
        0: options.USER_APPID,
        1: options.SERV_APPID
        }
    self.appKey = {
        0: options.USER_APPKEY,
        1: options.SERV_APPKEY
        }
    #self.__create_logger(name, port)
  
  def push(self, tobj):
    dobj = self.__translate_message(tobj)
    app_log.info("push json\t%s", dobj)
    
    ttype = tobj.template_type
    template = self.templateAction.get(ttype)(dobj)
    
    atype = tobj.app_type
    pusher = self.pusher.get(atype)
    
    ptype = tobj.push_type
    target = tobj.target if ptype == 1 else tobj.target[0]
    return self.pushAction.get(ptype)(pusher, template, target)

  def __translate_message(self, tobj):
    title = tobj.title
    app_log.info('push translate %s', title)
    return self.translateAction.get(title)(tobj)

  def __create_logger(self, name, port):
    datefmt = '%Y-%m-%d %H:%M:%S'
    timed_format = '%(asctime)s.%(msecs)d %(message)s'
    timedfmt = logging.Formatter(timed_format, datefmt=datefmt)
    
    file = name + str(port)
    handler = logging.handlers.TimedRotatingFileHandler(file, 'midnight')
    handler.setFormatter(timedfmt)

    self.log = logging.getLogger(name)
    self.log.addHandler(handler)

  def TranslatePoolOrder(self, tobj):
    d = {'ttype': tobj.template_type,
         'ptype': tobj.push_type,
         'title': u'包子拼车新订单信息', #tobj.title,
         'text':  u'有新的订单来了，赶快来抢吧', #tobj.text,
         'url':   tobj.url,
         'target':tobj.target,
         'APPID': self.appId[tobj.app_type],
         'APPKEY':self.appKey[tobj.app_type]
        }
    try:
      po = PoolOrder()
      po = deserialize(po, tobj.content)
      d['content'] = json.dumps( {'title':'poolorder', 'poolorder_id':po.id} ) 
    except Exception, e:
      app_log.error("deserialize thrift error, ", e)
    return d

  def TranslateConfirmOrder(self, tobj):
    d = {'ttype': tobj.template_type,
         'ptype': tobj.push_type,
         'title': tobj.title,
         'text':  tobj.text,
         'url':   tobj.url,
         'content': tobj.content,
         'target':tobj.target,
         'APPID': self.appId[tobj.app_type],
         'APPKEY':self.appKey[tobj.app_type]
        }
    return d

  def TranslateCancelOrder(self, tobj):
    d = {'ttype': tobj.template_type,
         'ptype': tobj.push_type,
         'title': tobj.title,
         'text':  tobj.text,
         'url':   tobj.url,
         'content': tobj.content,
         'target':tobj.target,
         'APPID': self.appId[tobj.app_type],
         'APPKEY':self.appKey[tobj.app_type]
        }
    return d
  
  def TranslateSystemNote(self, tobj):
    pass

#######################################################
def main():
  r = redis.StrictRedis(host=options.host, port=options.port)
  pc = PushCenter(options.log, options.pid)
  
  while (1):
    try:
      obj = r.brpop(options.queue, 1)
      if obj is None:
        time.sleep(1)
        continue

      msg = Message()
      msg = deserialize(msg, obj[1])
      ret = pc.push(msg)
      app_log.info("push result %s", ret)
      
      result = ret['result'].lower()
      if result != 'ok' and result != 'notarget':
        app_log.info('push failed this time, will re-push %s', obj[1])
        r.lpush(options.queue, obj[1])
    
    except Exception, e:
      app_log.error("push exception: %s", e)

if __name__ == '__main__':
  msg = Message()
  msg.template_type = 1;
  msg.push_type = 0;
  msg.app_type = 0;
  msg.title = "confirm_poolorder"
  msg.text = "test_text"
  msg.url = "http://www.12306.cn"
  jdict = { 'driver_phone': '123',
          'order_id': '456'}
  msg.content = json.dumps(jdict)
  msg.target = []
  bincode = serialize(msg)

  r = redis.StrictRedis(host=options.host, port=options.port)
  r.lpush(options.queue, bincode)

