import unittest
import test

if __name__ == '__main__':
  suites = test.all()
  runner = unittest.TextTestRunner(verbosity=2).run(suites)
