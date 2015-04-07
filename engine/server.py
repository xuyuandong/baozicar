#coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import tornado.ioloop
import tornado.web
import tornado.httpserver
from tornado.options import define, options

import redis
import os.path
import logging
import logging.handlers

import handlers
from handlers.test import *
from handlers.user import *
from handlers.driver import *
from handlers.center import *
from handlers.alipay import *

define("port", default=8801, help="http port", type=int)
define("debug", default=True, help="debug running mode")

define("redis_host", default="127.0.0.1", help="redis host")
define("redis_port", default=6379, help="redis port", type=int)

class Application(tornado.web.Application):
  def __init__(self):
    request_handlers = [
        (r"/", HomeHandler),
        (r"/get_authcode", GetAuthCodeHandler),
        (r"/feedback", FeedbackHandler),
        (r"/query_path", QueryPathHandler),
        (r"/query_price", QueryPriceHandler),
        (r"/alipay_notify", AlipayNotifyHandler),

        (r"/test_clear_system", TestClearSystemHandler),

        (r"/login_user", UserLoginHandler),
        (r"/save_profile", SaveProfileHandler),
        (r"/get_coupon_list", GetCouponListHandler),
        (r"/exchange_coupon", ExchangeCouponHandler),
        (r"/select_coupon", SelectCouponHandler),
        (r"/submit_order", SubmitOrderHandler),
        (r"/cancel_order", CancelOrderHandler),
        (r"/get_order_list", GetOrderListHandler),
        (r"/get_order_detail", GetOrderDetailHandler),
        (r"/submit_comment", SubmitCommentHandler),
        (r"/read_confirmed_order", ReadConfirmedOrderHandler),

        (r"/login_driver", DriverLoginHandler),
        (r"/change_driver_status", DriverChangeStatusHandler),
        (r"/change_driver_route", DriverChangeRouteHandler),
        (r"/get_poolorder_list", GetPoolOrderListHandler),
        (r"/get_poolorder_detail", GetPoolOrderDetailHandler),
        (r"/change_poolorder_status", ChangePoolOrderStatusHandler),
        (r"/read_pushed_poolorder", ReadPushedPoolOrderHandler),
        (r"/cancel_poolorder", CancelPoolOrderHandler),  
        (r"/get_driver_data", GetDriverDataHandler),  
    ]
    settings = dict(
      cookie_secret = "abcdefghijkmlnopqrstuvwxyz",
      template_path = os.path.join(os.path.dirname(__file__), "templates"),
      login_url = "/",
     # xsrf_cookies = True,
      debug = options.debug
      )

    self.db = handlers.DBUtil()
    self.log = handlers.LogUtil()
    self.push = handlers.PushUtil()

    self.redis = redis.ConnectionPool(
        host=options.redis_host,
        port=options.redis_port
        )

    self.alipay_public_key = open(options.alipay_public_key, 'r').read()

    tornado.web.Application.__init__(self, request_handlers, **settings)

def SetupLogger():
  format = '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d] %(message)s'
  formater = logging.Formatter(format, datefmt='%Y-%m-%d %H:%M:%S')
  
  log_file = 'app_log.%d' % (options.port)
  handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
  handler.setFormatter(formater)
  
  logging.getLogger("tornado.access").addHandler(handler)
  logging.getLogger("tornado.application").addHandler(handler)


if __name__ == "__main__":
  tornado.options.parse_command_line()
  SetupLogger()

  httpserver = tornado.httpserver.HTTPServer(Application(), xheaders=True)
  httpserver.listen(options.port)
  tornado.ioloop.IOLoop.instance().start()
