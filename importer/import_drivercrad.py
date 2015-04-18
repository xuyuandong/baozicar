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
define("mysql_db", default="statdb", help="mysql database")
define("mysql_user", default="root", help="mysql user")
define("mysql_password", default="showmeng1234", help="mysql password")

def usage():
  print "usage: %s versionfiles"%sys.argv[0]
  sys.exit(1)
	
if len(sys.argv) != 2:
  usage()

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

#def delete_dcard(db):
  #sql = "delete from cardb.t_version"
  #db.execute(sql)

def insert_dcard(db, v):
  sql = "insert into statdb.s_driver_moneyinfo \
    (phone, bankcardid ,deposit ,account_name) \
    values ('%s', '%s', '%s', '%s')"\
    %(v['phone'], v['bankcardid'], v['deposit'], v['account_name'])
  db.execute(sql)

def DECODE(s):
  line = s.strip().decode('gbk', 'utf-8')
  p2 = re.compile(ur'[^\u4e00-\u9fa5]')
  zh = string.join(p2.split(line)).strip()
  return zh

dcards = []
for fline in file(sys.argv[1]):
  fline = fline.strip('\r\n')
  flist = fline.split(',')
  v = {}
  v['phone'] = flist[0]
  v['bankcardid'] = flist[1]
  v['deposit'] = DECODE(flist[2])
  v['account_name'] = DECODE(flist[3])
  dcards.append(v)

if __name__ == '__main__':
  db = DBUtil()
  
  print dcards
  for v in dcards:
    print v
    insert_dcard(db, v)
