#!/usr/bin/python
#coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import re 

import time
import datetime
import string
import torndb
from tornado.options import define, options


define("mysql_host", default="/var/lib/mysql/mysql.sock", help="mysql host")
define("mysql_db", default="cardb", help="mysql database")
define("mysql_user", default="root", help="mysql user")
define("mysql_password", default="showmeng1234", help="mysql password")


class DBUtil:
  def __init__(self):
    self.conn = torndb.Connection(
      options.mysql_host, 
      options.mysql_db, 
      options.mysql_user, 
      options.mysql_password
      )
    
  def get(self, sql):
    return self.conn.get(sql)

  def query(self, sql):
    return self.conn.query(sql)

  def execute(self, sql):
    self.conn.execute(sql)


#DriverStatus = enum(online=0, offline=1, busy=2)
if __name__ == '__main__':
  db = DBUtil()
  
  table = "cardb.t_driver"
  sql = "select phone, from_city, to_city, status, priority from %s";
  objlist = db.query(sql)

  for obj in objlist:
    rkey = "z_driver_" + "-".join([obj.from_city, obj.to_city])
    opkey = "z_driver_" + "-".join([obj.to_city, obj.from_city])
    if obj.status == 0: # online
      db.r.zadd(rkey, obj.phone, obj.priority)
      db.r.zrem(opkey, obj.phone)
    elif obj.status == 1: # offline
      db.r.zrem(rkey, obj.phone)
      db.r.zrem(opkey, obj.phone)
    else: # busy
      pass


