# -*- coding: utf-8 -*-

from igt_push import *
from igetui.template import *
from igetui.template.igt_base_template import *
from igetui.template.igt_transmission_template import *
from igetui.template.igt_link_template import *
from igetui.template.igt_notification_template import *
from igetui.template.igt_notypopload_template import *
from igetui.template.igt_apn_template import *
from igetui.igt_message import *
from igetui.igt_target import *


HOST = 'http://sdk.open.api.igexin.com/apiex.htm'

class PushUtil(object):
  def __init__(self, APPID, APPKEY, MASTERSECRET):
    self.APPKEY = APPKEY
    self.APPID = APPID
    self.MASTERSECRET = MASTERSECRET
    self.push = IGeTui(HOST, self.APPKEY, self.MASTERSECRET)

  def ToSingle(self, template, dst, expire = 1000*3600*12):
    target = Target()
    target.appId = template.appId
    target.clientId = dst

    message = IGtSingleMessage()
    message.data = template
    message.isOffline = True
    message.pushNetWorkType = 0    
    message.offlineExpireTime = expire

    return self.push.pushMessageToSingle(message, target)

  def ToList(self, template, dst, expire = 1000*3600*12):
    def makeTarget(id):
      t = Target()
      t.appId = template.appId
      t.clientId = id
      return t
    targets = [makeTarget(cid) for cid in dst]

    message = IGtListMessage()
    message.data = template
    message.isOffline = True
    message.pushNetWorkType = 0
    message.offlineExpireTime = expire
    
    contentId = self.push.getContentId(message)
    return self.push.pushMessageToList(contentId, targets)

  def ToApp(self, template, dst, expire = 1000*3600*12):
    message = IGtAppMessage()
    message.data = template
    message.isOffline = True
    message.pushNetWorkType = 0
    message.offlineExpireTime = expire
    message.appIdList.extend([template.appId])
    return self.push.pushMessageToApp(message)
  
  #根据ClientID获取别名
  def queryAlias(self, cid):
    return self.push.queryAlias(self.APPID, cid)
  
  #根据别名获取ClientId
  def queryClientId(self, alias):
    return self.push.queryClientId(self.APPID, alias)

  #单个ClientId绑定别名
  def bindAlias(self, alias, cid):
    return self.push.bindAlias(self.APPID, alias, cid)

  #多个ClientIdn绑定一个别名
  def bindAliasBatch(self, alias, cidlist):
    def makeTarget(name, id):
      t = Target()
      t.clientId = id
      t.alias = name
      return t
    targets = [makeTarget(alias, cid) for cid in cidlist]
    return self.push.bindAliasBatch(self.APPID, targets)

  #解除Clientid与别名的绑定关系
  def unBindAlias(self, alias, cid):
    return self.push.unBindAlias(self.APPID, alias, cid)

  #取消别名下的所有ClientId绑定
  def unBindAliasAll(self, alias):
    return self.push.unBindAliasAll(self.APPID, alias)




