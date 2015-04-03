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

path = {
    'price': 200,
    'from_city': 'shenzhen',
    'to_city': 'guangzhou',
    'from_origin': 'FUCK',
    'to_origin': 'YOU',
    'from_lat': 40.12312314435,
    'from_lng': 116.2314356457,
    'to_lat': 42.13204030347,
    'to_lng': 117.23353379797,
    'from_discount': 3,
    'to_discount': 2,
    'from_step': 2,
    'to_step': 1.5,
    'from_scale': 1.2,
    'to_scale': 1.1,
    'driver_num': 10,
    'h17': 5
    }

driver = {
    'phone': '18603017596',
    'dev': '-',
    'name': 'yanhualiang',
    'image': '-',
    'license': '-',
    'carno': 'sb2587',
    'status': 1,
    'from_city': 'shenzhen',
    'to_city': 'guangzhou',
    'priority': 1
    }

db = DBUtil()

# insert driver
sql = "insert into cardb.t_driver \
    (phone, dev, name, image, license, carno, status, from_city, to_city, priority) \
    values ('%s', '%s', '%s', '%s', '%s', '%s', %s, '%s', '%s', %s)"\
    %(driver['phone'], driver['dev'], driver['name'], driver['image'], driver['license'],
        driver['carno'], driver['status'], driver['from_city'], driver['to_city'], driver['priority'])
db.execute(sql)


# insert path
rkey = 'path_' + '-'.join([path['from_city'], path['to_city']])
db.r.delete(rkey)
db.r.hmset(rkey, path)

# insert path
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
