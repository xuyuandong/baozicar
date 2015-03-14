#!/usr/bin/env python

import unittest

ALL_MODULES = [
    'test.user_test',
    ]

def all():
  return unittest.defaultTestLoader.loadTestsFromNames(ALL_MODULES)
