#coding=utf-8

import redis
import torndb
from tornado.options import define, options

define("mysql_host", default="/var/lib/mysql/mysql.sock", help="mysql host")
define("mysql_db", default="cardb", help="mysql database")
define("mysql_user", default="root", help="mysql user")
define("mysql_password", default="showmeng1234", help="mysql password")

define("redis_host", default="localhost", help="")
define("redis_port", default=6379, help="", type=int)

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

def insert_driver(db, driver):
  sql = "insert into cardb.t_driver \
    (phone, dev, name, image, license, carno, status, from_city, to_city, priority) \
    values ('%s', '%s', '%s', '%s', '%s', '%s', %s, '%s', '%s', %s)"\
    %(driver['phone'], driver['dev'], driver['name'], driver['image'], driver['license'],
        driver['carno'], driver['status'], driver['from_city'], driver['to_city'], driver['priority'])
  db.execute(sql)

def insert_path(db, path):
  sql = "insert into cardb.t_path \
    (price, from_city, to_city, from_origin, to_origin, \
    from_lat, from_lng, to_lat, to_lng, from_discount, to_discount, \
    from_step, to_step, from_scale, to_scale, driver_num) \
    values (%s, '%s', '%s', '%s', '%s', \
    %s, %s, %s, %s, %s, %s, \
    %s, %s, %s, %s, %s)"\
    %(path['price'], path['from_city'], path['to_city'], path['from_origin'], path['to_origin'],
      path['from_lat'], path['from_lng'], path['to_lat'], path['to_lng'], path['from_discount'], path['to_discount'],
      path['from_step'], path['to_step'], path['from_scale'], path['to_scale'], path['driver_num'])
  db.execute(sql)

  rkey = 'path_' + '-'.join([path['from_city'], path['to_city']])
  db.r.delete(rkey)
  db.r.hmset(rkey, path)


path1 = {
    'price': 35,
    'from_city': 'beijing',
    'to_city': 'langfang',
    'from_origin': '大羊坊桥',
    'to_origin': '采育路口',
    'from_lat': 39.819239,
    'from_lng': 116.521839,
    'to_lat': 39.670111,
    'to_lng': 116.682348,
    'from_discount': 10,
    'to_discount': 15,
    'from_step': 2,
    'to_step': 1.5,
    'from_scale': 1.2,
    'to_scale': 1.0,
    'driver_num': 4,
    }
path2 = {
    'price': 35,
    'from_city': 'langfang',
    'to_city': 'beijing',
    'to_origin': '大羊坊桥',
    'from_origin': '采育路口',
    'to_lat': 39.819239,
    'to_lng': 116.521839,
    'from_lat': 39.670111,
    'from_lng': 116.682348,
    'to_discount': 10,
    'from_discount': 15,
    'to_step': 2,
    'from_step': 1.5,
    'to_scale': 1.2,
    'from_scale': 1.0,
    'driver_num': 4,
    }

driver1 = {
    'phone': '13488858421',
    'dev': '-',
    'name': 'zhongshuanghua',
    'image': '-',
    'license': '-',
    'carno': 'hh5678',
    'status': 1,
    'from_city': 'beijing',
    'to_city': 'langfang',
    'priority': 1
    }
driver2 = {
    'phone': '15910601671',
    'dev': '-',
    'name': 'chengguihua',
    'image': '-',
    'license': '-',
    'carno': 'hh5679',
    'status': 1,
    'from_city': 'beijing',
    'to_city': 'langfang',
    'priority': 2
    }
driver3 = {
    'phone': '13051526700',
    'dev': '-',
    'name': 'pengchuang',
    'image': '-',
    'license': '-',
    'carno': 'hh5677',
    'status': 1,
    'from_city': 'beijing',
    'to_city': 'langfang',
    'priority': 3
    }
driver4 = {
    'phone': '15810750037',
    'dev': '-',
    'name': 'wuyunong',
    'image': '-',
    'license': '-',
    'carno': 'hh5680',
    'status': 1,
    'from_city': 'beijing',
    'to_city': 'langfang',
    'priority': 4
    }
driver5 = {
    'phone': '18688888888',
    'dev': '-',
    'name': 'yanhualiang',
    'image': '-',
    'license': '-',
    'carno': 'hh5688',
    'status': 1,
    'from_city': 'beijing',
    'to_city': 'langfang',
    'priority': 5
    }

if __name__ == '__main__':
  db = DBUtil()
  
  #insert_path(db, path1)
  #insert_path(db, path2)
  
  #insert_driver(db, driver1)
  #insert_driver(db, driver2)
  #insert_driver(db, driver3)
  insert_driver(db, driver5)


