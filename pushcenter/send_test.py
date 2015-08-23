# coding=utf-8
import sys                                      
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import time
import json
import redis
import logging

import tornado
import tornado.gen
from tornado.log import app_log
from tornado.options import define, options
from tornado.httpclient import HTTPClient, HTTPRequest

from thrift.TSerialization import * 
from genpy.scheduler.ttypes import *


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


#######################################################


def SendSms(target, content):
  phone = ','.join(target)
  bodylist= ['corp_id=7f24003',
        'corp_pwd=f24003',
        'corp_service=10690116yd',
        'mobile=' + phone.encode('gb2312'),
        'msg_content=' + content.encode('gb2312'),
        'corp_msg_id=authcode',
        'ext=8888']
  body = '&'.join(bodylist)

  url = 'http://service2.baiwutong.com:8080/sms_send2.do'
  client = HTTPClient()
  request = HTTPRequest(url, method='POST', body=body)
  return client.fetch(request)


#########################################################


if __name__ == '__main__':
  msg = Message()
  msg.template_type = 0
  msg.push_type = 2
  msg.app_type = 0
  msg.title = "confirm_poolorder"
  msg.text = "test_text"
  msg.url = "http://www.12306.cn"
  jdict = { 'driver_phone': '18926493053',
          'order_id': '5250459486852467596',
          'order_type': 1,
          'per_subsidy':50}
  msg.content = json.dumps(jdict)
  msg.target = ['18810308350']
  #msg.target = ['18603017596']
  bincode = serialize(msg)

  r = redis.StrictRedis(host=options.host, port=options.port)
  r.lpush(options.queue, bincode)


