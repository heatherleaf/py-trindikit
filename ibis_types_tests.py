# -*- encoding: utf-8 -*-

#
# ibis_types_tests.py
# Copyright (C) 2010, Alexander Berman. All rights reserved.
#
# This file contains unit tests for IBIS types.
#

from ibis import *
import unittest

class IbisTypesTests(unittest.TestCase):
    def test_Question(self):
        # Y/N questions
        q = Question("?return()")
        self.assertEquals(type(q), YNQ)
        self.assertEquals(q.prop.pred, Pred0("return"))

        # WHQ questions
        q = Question("?x.dest_city(x)")
        self.assertEquals(type(q), WhQ)
        self.assertEquals(q.pred, Pred1("dest_city"))

        # Alt questions
        q = AltQ(YNQ("city(paris)"), YNQ("city(london)"))
        self.assertEquals(type(q), AltQ)
        self.assertEquals(len(q.ynqs), 2)
        self.assertEquals(q.ynqs[0], YNQ("city(paris)"))
        self.assertEquals(q.ynqs[1], YNQ("city(london)"))

if __name__ == '__main__':
    unittest.main()
