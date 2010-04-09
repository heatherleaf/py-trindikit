# -*- encoding: utf-8 -*-

#
# ibis_tests.py
# Copyright (C) 2010, Alexander Berman. All rights reserved.
#
# This file contains unit tests for IBIS semantics.
#

from ibis import *
import unittest

class IbisTests(unittest.TestCase):
    preds0 = 'return'

    preds1 = {'price': 'int',
              'dest_city': 'city'}

    means = 'plane', 'train'
    cities = 'paris', 'london', 'berlin'

    sorts = {'means': means,
             'city': cities}

    domain = Domain(preds0, preds1, sorts)

    def test_relevant(self):
        ans = Answer("yes")
        que = Question("?return()")
        self.assertTrue(self.domain.relevant(ans.content, que))
        
        ans = Answer("no")
        que = Question("?return()")
        self.assertTrue(self.domain.relevant(ans.content, que))

        ans = Answer("paris")
        que = Question("?return()")
        self.assertFalse(self.domain.relevant(ans.content, que))

        ans = Answer("paris")
        que = Question("?x.dest_city(x)")
        self.assertTrue(self.domain.relevant(ans.content, que))

        ans = Answer("paris")
        que = Question("?x.price(x)")
        self.assertFalse(self.domain.relevant(ans.content, que))

if __name__ == '__main__':
    unittest.main()
