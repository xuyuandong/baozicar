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
    template.transmissionContent = '' #dobj['content']
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
# ttype: template type, 0: Transmission, 1: Notification, 2: Link
# ptype: push type, 0: App, 1: List, 2: Single
def enum(**enums):
  return type('Enum', (), enums)
TempType = enum(trans=0, notify=1, link=2)
PushType = enum(app=0, many=1, one=2)
AppType = enum(user=0, driver=1)

class PushCenter(object):
  def __init__(self):
    self.redis = redis.ConnectionPool(
        host=options.host,
        port=options.port
        )
    self.pusher = {
        AppType.user: PushUtil(options.USER_APPID, options.USER_APPKEY, options.USER_MASTERSECRET),
        AppType.driver: PushUtil(options.SERV_APPID, options.SERV_APPKEY, options.SERV_MASTERSECRET)
        }
    self.templateAction = {
        TempType.trans: GetTransmissionTemplate,
        TempType.notify: GetNotificationTemplate,
        TempType.link: GetLinkTemplate,
        }
    self.pushAction = {
        PushType.app: lambda p, temp, tar: p.ToApp(temp, tar),
        PushType.many: lambda p, temp, tar: p.ToList(temp, tar),
        PushType.one: lambda p, temp, tar: p.ToSingle(temp, tar)
        }
    self.translateAction = {
        'test': self.TranslateTest,
        'poolorder': self.TranslatePoolOrder,
        'confirm_poolorder': self.TranslateConfirmOrder,
        'cancel_poolorder': self.TranslateCancelOrder,
        'system_note': self.TranslateSystemNote
        }
    self.appId = {
        AppType.user: options.USER_APPID,
        AppType.driver: options.SERV_APPID
        }
    self.appKey = {
        AppType.user: options.USER_APPKEY,
        AppType.driver: options.SERV_APPKEY
        }
 
  @property
  def r(self):
    return redis.Redis(connection_pool = self.redis)

  def push(self, tobj):
    dobj = self.__translate_message(tobj)
    app_log.info("push json\t%s", dobj)
    
    atype = tobj.app_type
    pusher = self.pusher.get(atype)
    app_log.info("push atype %s", atype)

    ptype = tobj.push_type
    target = []
    if ptype == 1:
      target = tobj.target 
    elif ptype == 2:
      target = tobj.target[0]
    else:
      target = []
    app_log.info("push target %s", target)

    result = []
    for temp in dobj['ttype']:
      app_log.info("push template %s", temp)
      template = self.templateAction.get(temp)(dobj)
      ret = self.pushAction.get(ptype)(pusher, template, target)
      result.append(ret)

    return result

  def __translate_message(self, tobj):
    title = tobj.title
    app_log.info('push translate %s', title)
    return self.translateAction.get(title)(tobj)

  def TranslateTest(self, tobj):
    d = {'ttype': [tobj.template_type],
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

  def TranslatePoolOrder(self, tobj):
    d = {'ttype': [TempType.trans, TempType.notify],
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
    d = {'ttype': [TempType.trans, TempType.notify],
         'ptype': tobj.push_type,
         'title': u'包子拼车推送信息', #tobj.title,
         'text':  u'您的订单已有司机接单啦，赶紧查看吧', #tobj.text,
         'content': tobj.content,
         'url':   tobj.url,
         'target':tobj.target,
         'APPID': self.appId[tobj.app_type],
         'APPKEY':self.appKey[tobj.app_type]
        }
    return d

  def TranslateCancelOrder(self, tobj):
    d = {'ttype': [tobj.template_type],
         'ptype': tobj.push_type,
         'title': u'包子拼车推送信息', #tobj.title,
         'text':  u'您的订单已被司机取消，系统将重新为您安排司机，请查看详情', #tobj.text,
         'content': tobj.content,
         'url':   tobj.url,
         'target':tobj.target,
         'APPID': self.appId[tobj.app_type],
         'APPKEY':self.appKey[tobj.app_type]
        }
    return d

  def TranslateSystemNote(self, tobj):
    pass

#######################################################
def SetupLogger():
  format = '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d] %(message)s'
  formater = logging.Formatter(format, datefmt='%Y-%m-%d %H:%M:%S')
  
  log_file = 'app_log.%d' % (options.pid)
  handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
  handler.setFormatter(formater)
  
  logging.getLogger("tornado.application").addHandler(handler)

def main():
  SetupLogger()
    
  pc = PushCenter()
  
  while (1):
    obj = pc.r.brpop(options.queue, 5)
    if obj is None:
      time.sleep(5)
      continue

    try:
      msg = Message()
      msg = deserialize(msg, obj[1])
      results = pc.push(msg)
      
      success = True
      for ret in results:
        app_log.info("push result %s", ret)
        verb = ret['result'].lower()
        if verb != 'ok' and verb != 'notarget':
          app_log.info('push failed this time, will re-push %s', obj[1])
          success = False
          break
      
      if not success:
        pc.r.lpush(options.queue, obj[1])
    
    except Exception, e:
      app_log.error("push exception: %s", e)

 

if __name__ == '__main__':
  tornado.options.parse_command_line()
  main()
