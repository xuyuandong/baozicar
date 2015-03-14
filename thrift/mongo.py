import logging
import pymongo
import json

class MongoDB:
  def __init__(self, host="localhost", port=27017):
    conn = pymongo.Connection(host, port)
    self.conn = conn.conn
  
  def verify(self, name, pswd):
    info = self.conn.user.find_one({"name":name, "pswd":pswd})
    if info:
      return info["id"]
    else:
      return None

  def exist(self, name):
    info = self.conn.user.find_one({"name":name})
    if info:
      return True
    else:
      return False

  def insert(self, name, pswd):
    logging.info("request insert " + name + " " + pswd)
    info = {"name":name, "pswd":pswd, "id":name+pswd}
    self.conn.user.insert(info)
    return info["id"]

