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
  print "usage: %s driverfiles"%sys.argv[0]
  print "usage: %s d.csv"%sys.argv[0]
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


def select_driver(db, phone):
  sql = "select count(*) from cardb.t_driver where phone='%s'"%phone
  return db.query(sql)

def insert_driver(db, driver):
  #print "insert",driver['phone']
  sql = "insert into cardb.t_driver \
    (phone, dev, name, image, license, carno, status, from_city, to_city, priority) \
    values ('%s', '%s', '%s', '%s', '%s', '%s', %s, '%s', '%s', %s)"\
    %(driver['phone'], driver['dev'], driver['name'], driver['image'], driver['license'],
    driver['carno'], driver['status'], driver['from_city'], driver['to_city'], driver['priority'])
  db.execute(sql)
  
def update_driver(db, driver):
  #no priority
  #print driver['carno']
  sql = "update cardb.t_driver \
    set phone='%s', name='%s', image='%s', license='%s', carno='%s', status='%s', from_city='%s', to_city='%s'\
    where phone = %s"\
    %(driver['phone'], driver['name'], driver['image'], driver['license'],
    driver['carno'], driver['status'], driver['from_city'], driver['to_city'], driver['phone'])
  db.execute(sql)

def DECODE(s):
  line = s.strip().decode('gbk', 'utf-8')
  p2 = re.compile(ur'[^\u4e00-\u9fa5]')
  zh = string.join(p2.split(line)).strip()
  return zh

drivers = []
for fline in file(sys.argv[1]):
  fline = fline.strip('\r\n')
  flist = fline.split(',')
  d = {}
  d['phone'] = flist[0]
  d['dev'] = flist[1]
  d['name'] = DECODE(flist[2])
  d['image'] = flist[3]
  d['license'] = flist[4]
  #print DECODE(flist[5][:2])+flist[5][2:]
  d['carno'] = DECODE(flist[5][:2])+flist[5][2:]
  d['status'] = flist[6]
  d['from_city'] = DECODE(flist[7])
  d['to_city'] = DECODE(flist[8])
  d['priority'] = flist[9]
  #print d
  drivers.append(d)

if __name__ == '__main__':
  db = DBUtil()
  
  for d in drivers:
    if select_driver(db, d['phone'])[0]['count(*)'] == 0:
      insert_driver(db, d)
    else:
      update_driver(db, d)
