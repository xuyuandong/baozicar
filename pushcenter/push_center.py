# coding=utf-8
import sys                                      
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import time
import json
import redis
import random
import logging

import tornado
from tornado.log import app_log
from tornado.options import define, options

from thrift.TSerialization import * 
from genpy.scheduler.ttypes import *

################################

from push_template import *
from push_util import PushUtil 
from translator import Translator
from dbutil import DBUtil

from translator import TempType, PushType, AppType, OrderType

#toList接口每个用户返回用户状态开关,true：打开 false：关闭
os.environ['needDetails'] = 'true'

####################################################################

define("host", default = "redis1.ali", help = "")
define("port", default = 6379, help = "", type = int)
define("queue", default = "l_message", help = "")
define("retry_times", default=2, help="", type=int)
define("pid", default = 0, help = "process id", type = int)

define("USER_APPID", default = "qlZIF87hye8ZzyifZIEMn3", help = "")
define("USER_APPKEY", default = "WqJDqjvFPL9BBZ3NxIsNRA", help = "")
define("USER_APPSECRET", default = "QSfgiPT5YB9W4OrNp24hc5", help = "")
define("USER_MASTERSECRET", default = "FU1XLZGDlH9WA5u4j3nHA7", help = "")

define("SERV_APPID", default = "p35rm5CQNi8ELMOKsXnhqA", help = "")
define("SERV_APPKEY", default = "AbUz7mQ8k199NbT9yv6UB1", help = "")
define("SERV_APPSECRET", default = "HKxtQHnZjc9yqGbH021ET4", help = "")
define("SERV_MASTERSECRET", default = "XCfOSceoiM8lADovc9365A", help = "")



####################################################################
class PushCenter(object):
  def __init__(self):
    self.db = DBUtil()
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
    
    self.translator = Translator(self)
    self.translateAction = {
        'poolorder': self.translator.PoolOrder,
        'confirm_poolorder': self.translator.ConfirmPoolOrder,
        'cancel_booking_poolorder': self.translator.CancelBookingPoolOrder,
        'booking_deal': self.translator.BookingDeal,
        'system_notify': self.translator.SystemNotify
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
    title = tobj.title
    app_log.info('push translate %s', title)
    
    dobj = self.translateAction.get(title)(tobj)
    app_log.info("push json\t%s", dobj)
    
    pusher = self.pusher.get(tobj.app_type)
    app_log.info("push app_type %s", tobj.app_type)

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
      
      retry = options.retry_times
      while retry > 0:
        ret = self.pushAction.get(ptype)(pusher, template, target)
        app_log.info('try=%s ret=%s', retry, ret)
        verb = ret['result'].lower()
        if verb != 'ok' and verb != 'notarget':
          retry = retry - 1
        else:
          break

      result.append(ret)

    return result


#######################################################
def SetupLogger():
  format = '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d] %(message)s'
  formater = logging.Formatter(format, datefmt='%Y-%m-%d %H:%M:%S')
  
  log_file = 'app_log.%d' % (options.pid)
  handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
  handler.setFormatter(formater)
  
  logging.getLogger("tornado.application").addHandler(handler)


def PushOnce(pc, msg):
  success = True
  
  try:    
    results = pc.push(msg)
    for ret in results:
      verb = ret['result'].lower()
      if verb != 'ok' and verb != 'notarget':
        success = False
        break
  except Exception, e:
    app_log.error("push exception: %s", e)
    success = False
    
  return success


#########################################################
def main():
  SetupLogger()
  pc = PushCenter()
  
  while (1):
    obj = pc.r.brpop(options.queue, 5)
    if obj is None:
      time.sleep(5)
      continue

    msg = Message()
    msg = deserialize(msg, obj[1])
    random.shuffle(msg.target)
 
    ok = 0
    step = 10
    start = 0
    target = msg.target
    while len(target) > start:
      msg.target = target[start : start + step]
      start = start + step
      if PushOnce(pc, msg):
        ok = ok + 1
    
    if ok == 0:
      app_log.info('push message failed %s', msg.title)
      pc.r.lpush(options.queue, obj[1])
      
 
if __name__ == '__main__':
  tornado.options.parse_command_line()
  main()
