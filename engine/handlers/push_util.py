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
from tornado.options import define, options

#toList接口每个用户返回用户状态开关,true：打开 false：关闭
#os.environ['needDetails'] = 'true'

define("USER_APPID", default = "qlZIF87hye8ZzyifZIEMn3", help = "")
define("USER_APPKEY", default = "WqJDqjvFPL9BBZ3NxIsNRA", help = "")
define("USER_APPSECRET", default = "QSfgiPT5YB9W4OrNp24hc5", help = "")
define("USER_MASTERSECRET", default = "FU1XLZGDlH9WA5u4j3nHA7", help = "")

define("SERV_APPID", default = "p35rm5CQNi8ELMOKsXnhqA", help = "")
define("SERV_APPKEY", default = "AbUz7mQ8k199NbT9yv6UB1", help = "")
define("SERV_APPSECRET", default = "HKxtQHnZjc9yqGbH021ET4", help = "")
define("SERV_MASTERSECRET", default = "XCfOSceoiM8lADovc9365A", help = "")


HOST = 'http://sdk.open.api.igexin.com/apiex.htm'

class PushUtil(object):
  def __init__(self):
    self.pool = {
      0: Pusher(options.USER_APPID, options.USER_APPKEY, options.USER_MASTERSECRET),
      1: Pusher(options.SERV_APPID, options.SERV_APPKEY, options.SERV_MASTERSECRET)
      }

  @property
  def user(self):
    return self.pool.get(0)
  
  @property
  def driver(self):
    return self.pool.get(1)


class Pusher(object):
  def __init__(self, APPID, APPKEY, MASTERSECRET):
    self.APPID = APPID
    self.APPKEY = APPKEY
    self.MASTERSECRET = MASTERSECRET
    self.push = IGeTui(HOST, self.APPKEY, self.MASTERSECRET)

  def ToSingle(self, template, cid, expire = 1000*3600*12):
    target = Target()
    target.appId = self.APPID
    target.alias = cid
    #target.clientId = cid

    message = IGtSingleMessage()
    message.data = template
    message.isOffline = True
    message.pushNetWorkType = 0    
    message.offlineExpireTime = expire

    return self.push.pushMessageToSingle(message, target)

  def ToList(self, template, cidlist, expire = 1000*3600*12):
    def makeTarget(id):
      t = Target()
      t.appId = self.APPID
      t.alias = (id)
      #t.clientId = id
      return t
    targets = [makeTarget(cid) for cid in cidlist]

    message = IGtListMessage()
    message.data = template
    message.isOffline = True
    message.pushNetWorkType = 0
    message.offlineExpireTime = expire
    
    contentId = self.push.getContentId(message)
    return self.push.pushMessageToList(contentId, targets)

  def ToApp(self, template, expire = 1000*3600*12):
    message = IGtAppMessage()
    message.data = template
    message.isOffline = True
    message.pushNetWorkType = 0
    message.offlineExpireTime = expire
    message.appIdList.extend([self.APPID])
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
  def unbindAlias(self, alias, cid):
    return self.push.unBindAlias(self.APPID, alias, cid)

  #取消别名下的所有ClientId绑定
  def unbindAliasAll(self, alias):
    return self.push.unBindAliasAll(self.APPID, alias)


#数据经SDK传给客户端，由客户端代码觉得如何展现给用户
def GetTransmissionTemplate(obj):
    template = TransmissionTemplate()
    template.transmissionType = 1
    template.appId = obj['APPID']
    template.appKey = obj['APPKEY']
    template.transmissionContent = obj['content']
    #iOS 推送需要的PushInfo字段 前三项必填，后四项可以填空字符串
    #template.setPushInfo(actionLocKey, badge, message, sound, payload, locKey, locArgs, launchImage)
    #template.setPushInfo("",2,"","","","","","");
    return template

#通知栏显示含图标、标题、内容通知，点击后激活应用, IOS不推荐
def GetNotificationTemplate(obj):
    template = NotificationTemplate()
    template.appId = obj['APPID']
    template.appKey = obj['APPKEY']
    template.transmissionType = 1
    template.title = obj['title'] 
    template.text = obj['text']
    template.transmissionContent = obj['content']
    template.logo = "icon.png"
    template.logoURL = ""
    template.isRing = True
    template.isVibrate = True
    template.isClearable = True
    #iOS 推送需要的PushInfo字段 前三项必填，后四项可以填空字符串
    #template.setPushInfo("open",4,"message","","","","","");
    return template

#通知栏显示含图标、标题、内容通知，点击后打开指定网页，IOS不推荐
def GetLinkTemplate(obj):
    template = LinkTemplate()
    template.appId = obj['APPID']
    template.appKey = obj['APPKEY']
    template.title = obj['title']
    template.text = obj['text']
    template.logo = ""
    template.url = obj['url']
    template.transmissionType = 1
    template.transmissionContent = ''
    template.isRing = True
    template.isVibrate = True
    template.isClearable = True
    #iOS 推送需要的PushInfo字段 前三项必填，后四项可以填空字符串
    #template.setPushInfo("open",4,"message","test1.wav","","","","");
    return template



if __name__ == '__main__':
  pu = PushUtil()

  d = {
      'APPID':  options.USER_APPID,
      'APPKEY': options.USER_APPKEY,
      'title' : 'hello title',
      'text':   'hello text',
      'content':'hello content',
      'url':    'http://z.cn'
      }

  template = GetTransmissionTemplate(d)
  #print pu.user.ToApp(template)
  
  template = GetLinkTemplate(d) 
  #print pu.user.ToApp(template)

  template = GetNotificationTemplate(d)
  #print pu.user.ToApp(template)
 
  cid = 'a0b84826cff3602ad2783ad8dfcf8d7a'
  phone='18603017596'
  print pu.user.queryAlias(cid)
  print pu.user.bindAlias(phone, cid)
  print pu.user.unbindAliasAll(phone)

  print "push to single"
  #print pusher.ToSingle(template, "")

  print "push to list"
  #print pusher.ToList(template, [""])
