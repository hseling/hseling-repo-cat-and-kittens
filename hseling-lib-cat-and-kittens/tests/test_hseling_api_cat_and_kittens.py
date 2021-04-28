import unittest

import hseling_api_cat_and_kittens


class HSELing_API_Cat_and_kittensTestCase(unittest.TestCase):

    def setUp(self):
        self.app = hseling_api_cat_and_kittens.app.test_client()

    def test_index(self):
        rv = self.app.get('/')
        self.assertIn('Welcome to hseling_api_Cat and Kittens', rv.data.decode())


if __name__ == '__main__':
    unittest.main()
