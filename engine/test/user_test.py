#coding=utf-8

import json
import unittest
import tornado.testing
from tornado.testing import AsyncTestCase
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

class AuthcodeTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_authcode(self):
    client = AsyncHTTPClient(self.io_loop)
    return
    url = 'http://localhost/get_authcode?phone=18910068561'
    response = yield client.fetch(url)
    print response.body

class LoginTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_login(self):
    client = AsyncHTTPClient(self.io_loop)

    url = 'http://localhost/login_user'
    body='phone=18910068561&authcode=1833&dev_id=ABCDEFGH1234&push_id=12345678'
    #return
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)

    print response.body
    result = json.loads(response.body)
    self.assertEqual(result['status_code'], 200)

class SubmitOrderTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_submit(self):
    client = AsyncHTTPClient(self.io_loop)

    url = 'http://localhost/submit_order'
    bodylist=['token=MTg5MTAwNjg1NjE=|1422381603|49b62619e5e187693d6d29ebcb7f4ec388657782',
        'dev_id=ABCDEFGH1234',
        'order_type=1',
        'from_city=北京',
        'from_place=中关村',
        'to_city=华盛顿',
        'to_place=白宫',
        'person_num=3',
        'extra_msg=hello',
        'start_time=morning',
        'pay_id=ZFB123456',
        'total_price=20000',
        'fact_price=10000',
        'coupon_id=1',
        'coupon_price=10000']
    body = '&'.join(bodylist)
    return
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)

    print response.body
    result = json.loads(response.body)
    self.assertEqual(result['status_code'], 200)

class GetOrderListTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_get_order_list(self):
    client = AsyncHTTPClient(self.io_loop)

    url = 'http://localhost/get_order_list'
    bodylist=['token=MTg5MTAwNjg1NjE=|1422381603|49b62619e5e187693d6d29ebcb7f4ec388657782',
        'dev_id=ABCDEFGH1234',
        'date=20150202',
        'order_list_type=0']
    body = '&'.join(bodylist)
    return
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)

    result = json.loads(response.body)
    print json.dumps(result, indent = 2)
    self.assertEqual(result['status_code'], 200)

class CancelOrderTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_cancel_order(self):
    client = AsyncHTTPClient(self.io_loop)

    url = 'http://localhost/cancel_order'
    bodylist=['token=MTg5MTAwNjg1NjE=|1422381603|49b62619e5e187693d6d29ebcb7f4ec388657782',
        'dev_id=ABCDEFGH1234',
        'order_id=2']
    body = '&'.join(bodylist)
    return
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)

    print response.body
    result = json.loads(response.body)
    self.assertEqual(result['status_code'], 200)

if __name__ == '__main__':
  unittest.main()
