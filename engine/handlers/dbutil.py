#coding=utf-8

from tornado.options import define, options
import torndb

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
