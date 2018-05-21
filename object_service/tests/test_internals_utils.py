import sys
import os
from flask_testing import TestCase
from flask import request
from flask import url_for, Flask
import unittest
import requests
import time
from object_service import app
import json
import httpretty


class TestDataRetrieval(TestCase):

    '''Check if methods return expected results'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    def test_balanced_parentheses(self):
        '''Check the function that checks for balanced parentheses'''
        from object_service.utils import isBalanced
        # First give a test that should return True
        balanced = 'trending(references(citations(object:(Andromeda OR LMC) AND M1)))'
        self.assertTrue(isBalanced(balanced))
        # Now check an unbalanced example
        unbalanced = 'trending(references(citations(object:(Andromeda OR LMC AND M1)))'
        self.assertFalse(isBalanced(unbalanced))
        # No parentheses should return True
        noparenths = 'foo'
        self.assertTrue(isBalanced(noparenths))
        # Wrong order should return False
        test = ')x('
        self.assertFalse(isBalanced(test))

    def test_parse_query_string(self):
        '''Check is query string is parsed correctly'''
        from object_service.utils import parse_query_string
        # Unbalanced parentheses should return an empty list
        unbalanced = 'trending(references(citations(object:(Andromeda OR LMC AND M1)))'
        object_names, object_queries = parse_query_string(unbalanced)
        self.assertEqual(object_names, [])
        self.assertEqual(object_queries, [])

if __name__ == '__main__':
    unittest.main()