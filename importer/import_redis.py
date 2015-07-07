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
define("mysql_db", default="cardb", help="mysql database")
define("mysql_user", default="root", help="mysql user")
define("mysql_password", default="showmeng1234", help="mysql password")

define("redis_host", default="localhost", help="")
define("redis_port", default=6379, help="", type=int)

def usage():
  print "usage: %s pathfiles"%sys.argv[0]
  print "usage: %s p.csv"%sys.argv[0]
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


def refresh_redis_path(db, path):
  rkey = 'path_' + '-'.join([path['from_city'], path['to_city']])
  db.r.delete(rkey)
  db.r.hmset(rkey, path)

def refresh_redis_driver(db):
  sql = "select phone, from_city, to_city, status, priority from cardb.t_driver";
  objlist = db.query(sql)

  for obj in objlist:
    rkey = "z_driver_" + "-".join([obj.from_city, obj.to_city])
    opkey = "z_driver_" + "-".join([obj.to_city, obj.from_city])
    if obj.status == 0: # online
      db.r.zadd(rkey, obj.priority, obj.phone)
      db.r.zrem(opkey, obj.phone)
    elif obj.status == 1: # offline
      db.r.zrem(rkey, obj.phone)
      db.r.zrem(opkey, obj.phone)
    else: # busy
      pass
  
def DECODE(s):
  line = s.strip().decode('gbk', 'utf-8')
  p2 = re.compile(ur'[^\u4e00-\u9fa5]')
  zh = string.join(p2.split(line)).strip()
  return zh

if __name__ == '__main__':
  db = DBUtil()
  
  refresh_redis_driver(db)
  
  paths = []
  for fline in file(sys.argv[1]):
    fline = fline.strip('\r\n')
    flist = fline.split(',')
    p = {}
    #print flist
    p['pc_price'] = flist[0]
    p['bc_price'] = flist[1]
    p['from_pc_step'] = flist[2]
    p['to_pc_step'] = flist[3]
    p['from_bc_step'] = flist[4]
    p['to_bc_step'] = flist[5]
    p['from_city'] = DECODE(flist[6])
    #print DECODE(flist[6])
    #print p['from_city']
    p['to_city'] = DECODE(flist[7])
    p['from_origin'] = DECODE(flist[8])
    p['to_origin'] = DECODE(flist[9])
    p['from_lat'] = flist[10]
    p['from_lng'] = flist[11]
    p['to_lat'] = flist[12]
    p['to_lng'] = flist[13]
    p['from_discount'] = flist[14]
    p['to_discount'] = flist[15]
    p['from_scale'] = flist[16]
    p['to_scale'] = flist[17]
    p['driver_num'] = flist[18]
    #print p
    paths.append(p)
  
  for p in paths:
    refresh_redis_path(db, p)
  
