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
    def test_Atomic(self):
        # integer
        x = Ind(123)
        self.assertEquals(x.content, 123)
        self.assertNotEqual(x.content, "123")

        # string
        x = Ind("paris")
        self.assertEquals(x.content, "paris")
        self.assertRaises(AssertionError, Ind, "1paris")
        self.assertRaises(AssertionError, Ind, "p!aris")
        self.assertRaises(AssertionError, Ind, "paris()")
        x = Ind("paris_france")
        self.assertRaises(AssertionError, Ind, "_paris")

    def test_Ans(self):
        # proposition
        ans = Ans("city(paris)")
        self.assertEquals(type(ans), Prop)
        self.assertEquals(ans.pred, Pred1("city"))
        self.assertEquals(ans.ind.content, "paris")

        # short answer
        ans = Ans("paris")
        self.assertEquals(type(ans), ShortAns)
        self.assertEquals(ans.ind.content, "paris")

        # Y/N answer
        ans = Ans("yes")
        self.assertEquals(type(ans), YesNo)
        self.assertEquals(ans.yes, True)

        ans = Ans("no")
        self.assertEquals(type(ans), YesNo)
        self.assertEquals(ans.yes, False)

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
