# coding=utf-8
import sys                                      
reload(sys)
sys.setdefaultencoding('utf-8')

from igetui.template import *
from igetui.template.igt_base_template import *
from igetui.template.igt_transmission_template import *
from igetui.template.igt_link_template import *
from igetui.template.igt_notification_template import *
from igetui.template.igt_notypopload_template import *
from igetui.template.igt_apn_template import *

#数据经SDK传给客户端，由客户端代码觉得如何展现给用户
def GetTransmissionTemplate(dobj):
    template = TransmissionTemplate()
    template.transmissionType = 2
    template.appId = dobj['APPID']
    template.appKey = dobj['APPKEY']
    template.transmissionContent = dobj['content']
    #iOS 推送需要的PushInfo字段 前三项必填，后四项可以填空字符串
    #template.setPushInfo(actionLocKey, badge, message, sound, payload, locKey, locArgs, launchImage)
    #template.setPushInfo("",2,"","","","","","");
    return template

#通知栏显示含图标、标题、内容通知，点击后激活应用, IOS不推荐
def GetNotificationTemplate(dobj):
    template = NotificationTemplate()
    template.appId = dobj['APPID']
    template.appKey = dobj['APPKEY']
    template.transmissionType = 1
    template.title = dobj['title']
    template.text = dobj['text']
    template.transmissionContent = '' #dobj['content']
    template.logo = ""
    template.logoURL = ""
    template.isRing = True
    template.isVibrate = True
    template.isClearable = True
    #iOS 推送需要的PushInfo字段 前三项必填，后四项可以填空字符串
    #template.setPushInfo("open",4,"message","","","","","");
    return template

#通知栏显示含图标、标题、内容通知，点击后打开指定网页，IOS不推荐
def GetLinkTemplate(dobj):
    template = LinkTemplate()
    template.appId = dobj['APPID']
    template.appKey = dobj['APPKEY']
    template.title = dobj['title']
    template.text = dobj['text']
    template.logo = ""
    template.url = dobj['url']
    template.transmissionType = 1
    template.transmissionContent = dobj['content']
    template.isRing = True
    template.isVibrate = True
    template.isClearable = True
    #iOS 推送需要的PushInfo字段 前三项必填，后四项可以填空字符串
    #template.setPushInfo("open",4,"message","test1.wav","","","","");
    return template

