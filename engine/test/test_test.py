import unittest
import tornado.testing
from tornado.testing import AsyncTestCase
from tornado.httpclient import AsyncHTTPClient

class TestCase(AsyncTestCase):
  @tornado.testing.gen_test
  def test_select(self):
    client = AsyncHTTPClient(self.io_loop)
    response = yield client.fetch('http://localhost/test_select?username=yanhualiang')
    print response.body
    self.assertIn("abc123", response.body)

if __name__ == '__main__':
  unittest.main()
