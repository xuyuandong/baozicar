#coding=utf-8

from base import BaseHandler
import tornado.web
import tornado.gen
from tornado.log import app_log
from tornado.concurrent import run_on_executor
from futures import ThreadPoolExecutor
from push_util import *
import json

# /test_clear_system
class TestClearSystemHandler(BaseHandler):
  def get(self):
    keys = self.r.keys('z_driver_*')
    pipe  = self.r.pipeline(transaction=False)
    for key in keys:
      pipe.delete(key)
    pipe.execute()

    pipe.delete('h_order')
    pipe.delete('l_order')
    pipe.delete('h_carpool')
    pipe.delete('l_carpool')
    pipe.delete('h_history_driver')
    pipe.delete('h_lock')

# /test_add_driver
class TestAddDriverHandler(BaseHandler):
  def post(self):
    phone = self.get_argument('phone')
    dev_id = self.get_argument('dev_id')
    name = self.get_argument('name')
    from_city = self.get_argument('from_city')
    to_city = self.get_argument('to_city')
    priority = self.get_argument('priority')

    table = 'cardb.t_driver'
    sql = "insert into %s\
        (phone, dev, name, image, license, carno, \
        status, from_city, to_city, priority) \
        values ('%s', '%s', '%s', '', '', '',\
        0, '%s', '%s', %s);"%(phone, dev_id, name, from_city, to_city, priority)
    self.db.execute(sql)

    path_rpq = 'z_driver_' + '-'.join([from_city, to_city])
    self.r.zadd(path_rpq, phone=int(priority))


# /test_insert
class TestInsertHandler(BaseHandler):
  def get(self):
    username = self.get_argument("username")
    password = self.get_argument("password")
    description = self.get_argument("description")
    self.db.execute("insert into test_db.t_user (username, password, description)\
        values('%s','%s','%s')"%(username, password, description))
  def post(self):
    username = self.get_argument("username")
    password = self.get_argument("password")
    description = ""
    self.db.execute("insert into test_db.t_user (username, password, description)\
        values('%s','%s','%s')"%(username, password, description))

# /test_select
class TestSelectHandler(BaseHandler):
  def get(self):
    username = self.get_argument("username")
    object = self.db.get("select * from test_db.t_user where username='%s'"%(username))
    app_log.info(object)
    result = json.dumps(object, indent = 2)
    app_log.info(result)
    self.write(result)
  def post(self):
    username = self.get_argument("username")
    password = self.get_argument("password")
    object = self.db.query("select * from test_db.t_user \
        where username='%s' and password='%s'"%(username, password))
    app_log.info(object)
    result = json.dumps(object, indent = 2)
    app_log.info(result)
    self.write(result)

# /test_update
class TestUpdateHandler(BaseHandler):
  def get(self):
    username = self.get_argument("username")
    password = self.get_argument("password")
    self.db.execute('update test_db.t_user set password="%s"\
        where username="%s"'%(password, username))
  def post(self):
    username = self.get_argument("username")
    decription = self.get_argument("description")
    self.db.execute('update test_db.t_user set description="%s"\
        where username="%s"'%(username))

# /test_delete
class TestDeleteHandler(BaseHandler):
  def get(self):
    username = self.get_argument("username")
    self.db.execute('delete from test_db.t_user where username="%s"'%(username))
  def post(self):
    username = self.get_argument("username")
    self.db.execute('delete from test_db.t_user where username="%s"'%(username))

# /test_push
class TestPushHandler(BaseHandler):
  executor = ThreadPoolExecutor(4)

  @tornado.web.asynchronous
  @tornado.gen.coroutine
  def get(self):
    client = self.get_argument("client")
    content = "abc" #self.get_argument("content")
    template = GetLinkTemplate(content, content, 'http://z.cn')
    
    result = yield self.async_push(template, client)
    self.write(result)
    self.finish()

  @tornado.web.asynchronous
  @tornado.gen.coroutine
  def post(self):
    clients = self.get_argument("clients")
    content = self.get_argument("content")
    
    cidlist = clients.split(",")
    template = GetNotificationTemplate(content, content, content)

    result = yield self.async_push(template, cidlist)
    self.write(result)
    self.finish()

  @run_on_executor
  def async_push(self, template, target):
    if isinstance(target, list):
      return self.push.ToList(template, target)
    else:
      return self.push.ToSingle(template, target)
