#coding=utf-8

import logging
from tornado.options import define, options

define("reqlog", default="logs/req.log.", help="req logs")
define("paylog", default="logs/pay.log.", help="pay logs")

class LogUtil(object):
  def __init__(self):
    datefmt = '%Y-%m-%d %H:%M:%S'
    timed_format = '%(asctime)s.%(msecs)d %(message)s'
    self.timedfmt = logging.Formatter(timed_format, datefmt=datefmt)
    
    self.reqlog = self.__create_logger(options.reqlog, options.port)
    self.paylog = self.__create_logger(options.paylog, options.port)

  def __create_logger(self, name, port):
    file = name + str(port)
    
    handler = logging.handlers.TimedRotatingFileHandler(file, 'midnight')
    handler.setFormatter(self.timedfmt)

    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger

