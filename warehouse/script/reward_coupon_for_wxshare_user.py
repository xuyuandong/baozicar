#!/usr/bin/python
#coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import re 

import time
import datetime
import string
import redis
import torndb
from tornado.options import define, options

define("mysql_host", default="/var/lib/mysql/mysql.sock", help="mysql host")
#define("mysql_host", default="hrdsjqqyabiqvfav.mysql.rds.aliyuncs.com", help="mysql host")
define("mysql_db", default="cardb", help="mysql database")
define("mysql_user", default="root", help="mysql user")
define("mysql_password", default="showmeng1234", help="mysql password")

define("redis_host", default="localhost", help="")
define("redis_port", default=6379, help="", type=int)

#############################################

class DBUtil:
  def __init__(self):
    self.conn = torndb.Connection(
      options.mysql_host, 
      options.mysql_db, 
      options.mysql_user, 
      options.mysql_password
      )
    self.r = redis.StrictRedis(host=options.redis_host, port=options.redis_port)
    
  def get(self, sql):
    return self.conn.get(sql)

  def query(self, sql):
    return self.conn.query(sql)

  def execute(self, sql):
    self.conn.execute(sql)
	
  @property
  def r(self):
    return self.r

def uuid(phone):
  t = datetime.datetime.now()
  y = t.year%10
  d = t.day + 31*t.month
  s = t.hour*3600 + t.minute*60 + t.second
  r = phone[-4:]
  ret = '%s%03s%05s%06s%04s'%(y,d,s, t.microsecond, r)
  return int(ret.replace(' ', '0'))


def fetch_reward_user(beg_day, end_day):
  # t_order.status == 2 means order toeval (instead of done)
  sql="select TA.phone as use_phone, TB.code as coupon_code \
       from t_order TA join t_coupon TB \
       on (TA.coupon_id = TB.id) \
       where TA.status = 2 and TB.code != 0 and \
       TA.dt >= '%s 00:00:00' and TA.dt < '%s 00:00:00'"%(beg_day, end_day)

  print sql
  sql2="select TA.phone as share_phone, TB.use_phone \
       from t_wxshare_app TA join (%s) TB \
       on (TA.code = TB.coupon_code);"%(sql)

  print sql2

  db = DBUtil()
  objlist = db.query(sql2)

  result = []
  for obj in objlist:
    if obj.share_phone != obj.use_phone:
      result.append(obj.share_phone)
  return result


def reward_user_coupons(phone_list):
  deadline = datetime.datetime.now() + datetime.timedelta(days = 30)
  coupon = {'ctype': -1,
      'price': 15,
      'within': 0,
      'deadline': deadline.strftime('%Y-%m-%d'),
      'note': u'微信推荐乘客乘车后回报奖励'}
  table = 'cardb.t_coupon'

  db = DBUtil()
  for phone in phone_list:
    coupon_id = uuid(phone)
    sql = "insert into %s (id, ctype, status, price, within, deadline, note, phone, code, dt) \
        values(%s, %s, %s, %s, %s, '%s', '%s', '%s', %s, null)" \
        %(table, coupon_id, coupon['ctype'], 0, coupon['price'], \
        coupon['within'], coupon['deadline'], coupon['note'], phone, 0)
    db.execute(sql)
    

if __name__ == '__main__':
  end = datetime.datetime.now()
  begin = end + datetime.timedelta(days = -10)

  beg_day = begin.strftime('%Y-%m-%d')
  end_day = end.strftime('%Y-%m-%d')
  print beg_day
  print end_day
  
  users = fetch_reward_user(beg_day, end_day)
  print users
  
  reward_user_coupons(users)
