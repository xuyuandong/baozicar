#coding=utf-8

from tornado.options import define, options
import torndb

define("mysql_host", default="rdsjqqyabiqvfav.mysql.rds.aliyuncs.com", help="mysql host")
define("mysql_user", default="baoziapp", help="mysql user")
define("mysql_password", default="eGsDyJFCVKFM5ZsM", help="mysql password")
define("mysql_db", default="cardb", help="mysql database")

class DBUtil:
  def __init__(self):
    self.connect()

  def connect(self):
    self.conn = torndb.Connection(
        options.mysql_host, 
        options.mysql_db, 
        options.mysql_user, 
        options.mysql_password,
        60, #max_idle_time
        1,  #connect_timeout
        '+8:00' 
        )
  
  def get(self, sql):
    return self.conn.get(sql)

  def query(self, sql):
    return self.conn.query(sql)

  def execute(self, sql):
    self.conn.execute(sql)
