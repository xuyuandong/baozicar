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

    url = 'http://localhost/get_authcode?phone=15810750037'
    response = yield client.fetch(url)
    
    print response.body
    self.assertIn('authcode', response.body)

class LoginTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_login(self):
    client = AsyncHTTPClient(self.io_loop)

    url = 'http://localhost/login_driver'
    body='phone=15810750037&authcode=7551&dev_id=ABCDEFGH5678&push_id=98765432'
    return
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)

    print response.body
    result = json.loads(response.body)
    self.assertEqual(result['status_code'], 200)

class ConfirmTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_change_poolorder_status(self):
    client = AsyncHTTPClient(self.io_loop)

    url = 'http://localhost/change_poolorder_status'
    bodylist= ['token=MTU4MTA3NTAwMzc=|1422732578|f2b272a876a91dd7b9cba61f6a618bd0a79593b5',
        'dev_id=ABCDEFGH5678',
        'status=1',
        'poolorder_id=90ac391c-599e-4a18-bdd2-cab448c8d466']
    body = '&'.join(bodylist)
    return 
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)

    print response.body
    result = json.loads(response.body)
    self.assertEqual(result['status_code'], 200)

class UnfreezeTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_change_poolorder_status(self):
    client = AsyncHTTPClient(self.io_loop)

    url = 'http://localhost/change_poolorder_status'
    bodylist= ['token=MTU4MTA3NTAwMzc=|1422732578|f2b272a876a91dd7b9cba61f6a618bd0a79593b5',
        'dev_id=ABCDEFGH5678',
        'status=2',
        'poolorder_id=90ac391c-599e-4a18-bdd2-cab448c8d466']
    body = '&'.join(bodylist)
    return 
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)

    print response.body
    result = json.loads(response.body)
    self.assertEqual(result['status_code'], 200)

class DoneTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_change_poolorder_status(self):
    client = AsyncHTTPClient(self.io_loop)

    url = 'http://localhost/change_poolorder_status'
    bodylist= ['token=MTU4MTA3NTAwMzc=|1422732578|f2b272a876a91dd7b9cba61f6a618bd0a79593b5',
        'dev_id=ABCDEFGH5678',
        'status=4',
        'poolorder_id=90ac391c-599e-4a18-bdd2-cab448c8d466']
    body = '&'.join(bodylist)
    return
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)

    print response.body
    result = json.loads(response.body)
    self.assertEqual(result['status_code'], 200)

class CancelTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_change_poolorder_status(self):
    client = AsyncHTTPClient(self.io_loop)

    url = 'http://localhost/change_poolorder_status'
    bodylist= ['token=MTU4MTA3NTAwMzc=|1422732578|f2b272a876a91dd7b9cba61f6a618bd0a79593b5',
        'dev_id=ABCDEFGH5678',
        'status=5',
        'poolorder_id=5f50298a-6c6e-448b-b2a8-1de273744da0']
        #'poolorder_id=90ac391c-599e-4a18-bdd2-cab448c8d466']
    body = '&'.join(bodylist)
    return
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)

    print response.body
    result = json.loads(response.body)
    self.assertEqual(result['status_code'], 200)

class GetPoolOrderListTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_get_poolorder_list(self):
    client = AsyncHTTPClient(self.io_loop)

    url = 'http://localhost/get_poolorder_list'
    bodylist= ['token=MTU4MTA3NTAwMzc=|1422732578|f2b272a876a91dd7b9cba61f6a618bd0a79593b5',
        'dev_id=ABCDEFGH5678',
        'poolorder_list_type=2',
        'date=20150204']
    body = '&'.join(bodylist)
    return 
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)

    print response.body
    result = json.loads(response.body)
    self.assertEqual(result['status_code'], 200)

class GetPoolOrderDetailTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_get_poolorder_detail(self):
    client = AsyncHTTPClient(self.io_loop)

    url = 'http://localhost/get_poolorder_detail'
    bodylist= ['token=MTU4MTA3NTAwMzc=|1422732578|f2b272a876a91dd7b9cba61f6a618bd0a79593b5',
        'dev_id=ABCDEFGH5678',
        'date=20150204',
        'poolorder_id=90ac391c-599e-4a18-bdd2-cab448c8d466']
    body = '&'.join(bodylist)
    
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)

    print response.body
    result = json.loads(response.body)
    self.assertEqual(result['status_code'], 200)

class ChangeDriverRouteTeseCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_change_driver_route(self):
    client = AsyncHTTPClient(self.io_loop)

    url = 'http://localhost/change_driver_route'
    bodylist= ['token=MTU4MTA3NTAwMzc=|1422732578|f2b272a876a91dd7b9cba61f6a618bd0a79593b5',
        'dev_id=ABCDEFGH5678',
        'from_city=纽约',
        'to_city=北京']
    body = '&'.join(bodylist)
    return
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)

    print response.body
    result = json.loads(response.body)
    self.assertEqual(result['status_code'], 200)

class ChangeDriverStatusTestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_change_driver_status(self):
    client = AsyncHTTPClient(self.io_loop)

    url = 'http://localhost/change_driver_status'
    bodylist= ['token=MTU4MTA3NTAwMzc=|1422732578|f2b272a876a91dd7b9cba61f6a618bd0a79593b5',
        'dev_id=ABCDEFGH5678',
        'status=1']
    body = '&'.join(bodylist)
    return
    request = HTTPRequest(url, method='POST', body=body)
    response = yield client.fetch(request)

    print response.body
    result = json.loads(response.body)
    self.assertEqual(result['status_code'], 200)


if __name__ == '__main__':
  unittest.main()
