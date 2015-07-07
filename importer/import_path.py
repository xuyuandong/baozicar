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
    
  def get(self, sql):
    return self.conn.get(sql)

  def query(self, sql):
    return self.conn.query(sql)

  def execute(self, sql):
    self.conn.execute(sql)

def delete_path(db):
  sql = "delete from cardb.t_path"
  db.execute(sql)

def insert_path(db, path):
  sql = "insert into cardb.t_path \
    (pc_price, bc_price, from_pc_step, to_pc_step, \
    from_bc_step, to_bc_step, \
    from_city, to_city, from_origin, to_origin, \
    from_lat, from_lng, to_lat, to_lng, from_discount, to_discount, \
    from_scale, to_scale, driver_num) \
    values (%s, %s, %s, %s,\
    %s, %s, \
    '%s', '%s', '%s', '%s', \
    %s, %s, %s, %s, %s, %s, \
    %s, %s, %s)"\
    %(path['pc_price'], path['bc_price'], path['from_pc_step'], path['to_pc_step'],
    path['from_bc_step'], path['to_bc_step'],
    path['from_city'], path['to_city'], path['from_origin'], path['to_origin'],
    path['from_lat'], path['from_lng'], path['to_lat'], path['to_lng'], 
    path['from_discount'], path['to_discount'],
    path['from_scale'], path['to_scale'], path['driver_num'])
  db.execute(sql)

def DECODE(s):
  line = s.strip().decode('gbk', 'utf-8')
  p2 = re.compile(ur'[^\u4e00-\u9fa5]')
  zh = string.join(p2.split(line)).strip()
  return zh

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

if __name__ == '__main__':
  db = DBUtil()
  
  delete_path(db)
  for p in paths:
    insert_path(db, p)

