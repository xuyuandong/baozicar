#coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import json
import unittest
import tornado.testing
from tornado.testing import AsyncTestCase
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

class LoginTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_login(self):
    phone = '15810750037'
    content='尊敬的用户，您好！感谢您选择包子拼车，包子拼车验证码990988已发送到您手机上，美好城市绿色出行，包子拼车为您导航。'
    print content

    url = 'http://service2.baiwutong.com:8080/sms_send2.do'
    bodylist= ['corp_id=7f24003',
        'corp_pwd=f24003',
        'corp_service=10690116yd',
        'mobile=%s'%(phone.encode('gb2312')),
        'msg_content=%s'%(content.encode('gb2312')),
        'corp_msg_id=test',
        'ext=8888']
    body = '&'.join(bodylist)
    print body
    return
    client = AsyncHTTPClient(self.io_loop)
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)

    print response.body


class QueryPriceTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_price(self):
    from_place = '金码大厦'
    from_city = '北京'
    from_params = ['origin=%s'%(from_place),
        'destination=%s'%(from_city),
        'origin_region=%s'%(from_city),
        'destination_region=%s'%(from_city)]

    baidu_ak = 'ak=286e2613aa2e671c497b40cdcc5f06e7'
    baidu_url = 'http://api.map.baidu.com/direction/v1?mode=driving&output=json&'
    params.append(baidu_ak)
    url = baidu_url + '&'.join(params)

    client = AsyncHTTPClient(self.io_loop)
    response = yield client.fetch(url)
    print response.body

if __name__ == '__main__':
  unittest.main()
