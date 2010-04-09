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
        # Y/N questions
        que = Question("?return()")

        ans = Answer("yes")
        self.assertTrue(self.domain.relevant(ans.content, que))
        
        ans = Answer("no")
        self.assertTrue(self.domain.relevant(ans.content, que))

        ans = Answer("paris")
        self.assertFalse(self.domain.relevant(ans.content, que))


        # WHQ questions
        que = Question("?x.dest_city(x)")

        ans = Answer(ShortAns(Ind('paris'), True)) # "paris"
        self.assertTrue(self.domain.relevant(ans.content, que))

        ans = Answer(ShortAns(Ind('paris'), False)) # "not paris"
        self.assertTrue(self.domain.relevant(ans.content, que))

        ans = Answer("dest_city(paris)")
        self.assertTrue(self.domain.relevant(ans.content, que))

        ans = Answer(ShortAns(Ind('five'), True)) # "five"
        self.assertFalse(self.domain.relevant(ans.content, que))

        ans = Answer(ShortAns(Ind('five'), False)) # "not five"
        self.assertFalse(self.domain.relevant(ans.content, que))


    def test_resolves(self):
        # Y/N questions
        que = Question("?return()")

        ans = Answer("yes")
        self.assertTrue(self.domain.resolves(ans.content, que))
        
        ans = Answer("no")
        self.assertTrue(self.domain.resolves(ans.content, que))

        ans = Answer("paris")
        self.assertFalse(self.domain.resolves(ans.content, que))


        # WHQ questions
        que = Question("?x.dest_city(x)")

        ans = Answer(ShortAns(Ind('paris'), True)) # "paris"
        self.assertTrue(self.domain.resolves(ans.content, que))

        ans = Answer(ShortAns(Ind('paris'), False)) # "not paris"
        self.assertFalse(self.domain.resolves(ans.content, que))

        ans = Answer("dest_city(paris)")
        self.assertTrue(self.domain.resolves(ans.content, que))

        ans = Answer(ShortAns(Ind('five'), True)) # "five"
        self.assertFalse(self.domain.resolves(ans.content, que))

        ans = Answer(ShortAns(Ind('five'), False)) # "not five"
        self.assertFalse(self.domain.resolves(ans.content, que))


    def test_combine(self):
        # Y/N questions
        que = Question("?return()")

        ans = Answer("yes")
        res = Prop(Pred0('return'), None, True)
        self.assertEqual(self.domain.combine(que, ans.content), res)

        ans = Answer("no")
        res = Prop(Pred0('return'), None, False)
        self.assertEqual(self.domain.combine(que, ans.content), res)


        # WHQ questions
        que = Question("?x.dest_city(x)")

        ans = Answer(ShortAns(Ind('paris'), True)) # "paris"
        res = Prop(Pred1('dest_city'), Ind('paris'), True)
        self.assertEqual(self.domain.combine(que, ans.content), res)

        ans = Answer(ShortAns(Ind('paris'), False)) # "not paris"
        res = Prop(Pred1('dest_city'), Ind('paris'), False)
        self.assertEqual(self.domain.combine(que, ans.content), res)

        ans = Answer("dest_city(paris)")
        res = Prop(Pred1('dest_city'), Ind('paris'), True)
        self.assertEqual(self.domain.combine(que, ans.content), res)

if __name__ == '__main__':
    unittest.main()
