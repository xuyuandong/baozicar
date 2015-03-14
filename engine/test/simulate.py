#coding=utf-8

import redis
import tornado.web
import tornado.ioloop

from tornado.options import define, options
from dbutil import DBUtil


class Simulator(object):
  def __init__(self):
    self.db = DBUtil()
    self.redis = redis.StrictRedis(
        host=options.redis_host,
        port=options.redis_port)
    self.io_loop = ioloop.IOLoop.instance()

  def load_driver(self, infile):
    with open(infile) as f:
      for line in f:
        ts = line.strip().split(' ')
        if len(ts) < 6:
          print 'error driver:', line.strip()
          continue
        self.load_driver_impl(ts)

  def load_user(self, infile):
    with open(infile) as f:
      for line in f:
        ts = line.strip().split(' ')
        if len(ts) < 3:
          print 'error user:', line.strip()
          continue
        self.load_user_impl(ts)

  def load_driver_impl(self, ts):
    phone, dev_id, name, from_city, to_city, priority = ts

    table = 'cardb.t_driver'
    sql = "insert into %s\
        (phone, dev, name, image, license, carno, \
        status, from_city, to_city, priority) \
        values ('%s', '%s', '%s', '', '', '',\
        0, '%s', '%s', %s);"
        %(phone, dev_id, name, from_city, to_city, priority)
    self.db.execute(sql)

    path_rpq = 'z_driver_' + '-'.join([from_city, to_city])
    self.r.zadd(path_rpq, phone=int(priority))

  def load_user_impl(self, ts):
    phone, dev_id, push_id = ts

    url = 'http://localhost/login_user'
    body='phone=%s&authcode=7551&dev_id=%s&push_id=%s'%(phone, dev_id, push_id)

    client = AsyncHTTPClient(self.io_loop)
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)
    result = json.loads(response.body)

    print phone, dev_id, push_id, result['token']

  def clear(self):
    keys = self.r.keys('z_driver_*')
    for key in keys:
      self.r.delete(key)
    self.r.delete('h_order')
    self.r.delete('l_order')
    self.r.delete('h_carpool')
    self.r.delete('l_carpool')
    self.r.delete('h_history_driver')
    self.r.delete('h_lock')

if __name__ == '__main__':
  pass

