#coding: utf-8

import json
import string

from igetui.protobuf import *


class BaseTemplate:
    def __init__(self):
        self.appKey = ""
        self.appId = ""
        self.pushInfo = None

    def getTransparent(self):
        transparent = gt_req_pb2.Transparent()
        transparent.id = ""
        transparent.action = "pushmessage"
        transparent.taskId = ""
        transparent.appKey = self.appKey
        transparent.appId = self.appId
        transparent.messageId = ""
        transparent.pushInfo.CopyFrom(self.getPushInfo())
        actionChains = self.getActionChains()
        for actionChain in actionChains:
            tmp = transparent.actionChain.add()
            tmp.CopyFrom(actionChain)
        return transparent

    def getActionChains(self):
        return []

    def getPushInfo(self):
        if self.pushInfo is None:
            self.pushInfo = gt_req_pb2.PushInfo()
            self.pushInfo.message = ""
            self.pushInfo.actionKey = ""
            self.pushInfo.sound = ""
            self.pushInfo.badge = "-1"
        return self.pushInfo

    def setPushInfo(self, actionLocKey, badge, message, sound, payload, locKey, locArgs, launchImage,
                    contentAvailable=0):
        self.pushInfo = gt_req_pb2.PushInfo()
        self.pushInfo.actionLocKey = actionLocKey.decode("utf-8")
        self.pushInfo.badge = str(badge)
        self.pushInfo.message = message.decode("utf-8")
        self.pushInfo.sound = sound.decode("utf-8")
        self.pushInfo.payload = payload.decode("utf-8")
        self.pushInfo.locKey = locKey.decode("utf-8")
        self.pushInfo.locArgs = locArgs.decode("utf-8")
        self.pushInfo.launchImage = launchImage.decode("utf-8")
        self.pushInfo.contentAvailable = contentAvailable

        isValidate = self.validatePayload(locKey, locArgs, message, actionLocKey, launchImage, str(badge), sound,
                                          payload, contentAvailable)
        # print self.validatePayloadLength(locKey, locArgs, message, actionLocKey, launchImage, str(badge), sound,
        #                            payload)
        if isValidate is False:
            payloadLen = self.validatePayloadLength(locKey, locArgs, message, actionLocKey, launchImage, str(badge),
                                                    sound, payload, contentAvailable)
            raise Exception("PushInfo length over limit: " + str(payloadLen) + ". Allowed: 256.")

    def validatePayload(self, locKey, locArgs, message, actionLocKey, launchImage, badge, sound, payload,
                        contentAvailable):
        length = self.validatePayloadLength(locKey, locArgs, message, actionLocKey, launchImage, badge, sound, payload,
                                            contentAvailable)
        return length <= 256

    def validatePayloadLength(self, locKey, locArgs, message, actionLocKey, launchImage, badge, sound, payload,
                              contentAvailable):
        json = self.processPayload(locKey, locArgs, message, actionLocKey, launchImage, badge, sound, payload,
                                   contentAvailable)
        # print json
        return len(json)

    def toInt(self, strr, defaultValue):
        if strr is None or strr == "":
            return defaultValue
        return int(strr)

    def processPayload(self, locKey, locArgs, message, actionLocKey, launchImage, badge, sound, payload,
                       contentAvailable):
        isValid = False
        pb = self.Payload()
        if locKey is not None and len(locKey) > 0:
            pb.alertLocKey = locKey
            if locArgs is not None and len(locArgs) > 0:
                pb.alertLocArgs = locArgs.split(",")
            isValid = True

        if message is not None and len(message) > 0:
            pb.alertBody = message
            isValid = True

        if actionLocKey is not None and len(actionLocKey) > 0:
            pb.alertActionLocKey = actionLocKey

        if launchImage is not None and len(launchImage) > 0:
            pb.alertLaunchImage = launchImage

        badgeNum = -1
        try:
            badgeNum = int(badge)
        except:
            pass

        if badgeNum >= 0:
            pb.badge = badgeNum
            isValid = True

        if sound is not None and len(sound) > 0:
            pb.sound = sound
        else:
            pb.sound = "default"

        if payload is not None and len(payload) > 0:
            pb.addParam("payload", payload)

        if contentAvailable == 1:
            pb.contentAvailable = 1
            isValid = True

        if not isValid:
            raise Exception("one of the params(locKey,message,badge) must not be null or contentAvailable must be 1")

        json = pb.toString()

        if json is None:
            raise Exception("payload json is null")

        return json

    class Payload:
        def __init__(self):
            self.APS = "aps"
            self.params = None
            self.alert = None
            self.badge = None
            self.sound = ""
            self.alertBody = None
            self.alertActionLocKey = None
            self.alertLocKey = None
            self.alertLocArgs = None
            self.alertLaunchImage = None
            self.contentAvailable = None

        def addParam(self, key, obj):
            if self.params is None:
                self.params = {}
            if self.APS == key.lower():
                raise Exception("the key can't be aps")
            self.params[key] = obj

        def putIntoJson(self, key, value, obj):
            if value is not None:
                obj[key] = value

        def toString(self):
            objectt = {}
            apsObj = {}

            if self.alert is not None:
                apsObj["alert"] = self.alert
            else:
                if self.alertBody is not None or self.alertLocKey is not None:
                    alertObj = {}
                    self.putIntoJson("body", self.alertBody, alertObj)
                    self.putIntoJson("action-loc-key", self.alertActionLocKey, alertObj)
                    self.putIntoJson("loc-key", self.alertLocKey, alertObj)
                    self.putIntoJson("launch-image", self.alertLaunchImage, alertObj)
                    if self.alertLocArgs is not None:
                        array = []
                        for strr in self.alertLocArgs:
                            array.append(strr)
                        alertObj["loc-args"] = array
                    apsObj["alert"] = alertObj

                if self.badge is not None:
                    apsObj["badge"] = self.badge

                if self.sound != "com.gexin.ios.silence":
                    self.putIntoJson("sound", self.sound, apsObj)
                if self.contentAvailable == 1:
                    apsObj["content-available"] = 1
                objectt[self.APS] = apsObj

                if self.params is not None:
                    for k, v in self.params.items():
                        objectt[k] = v

                jsonData = json.dumps(objectt, separators=(',', ':'), ensure_ascii=False)
                return jsonData
