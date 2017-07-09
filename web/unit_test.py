from app import *
import unittest 

class FlaskBookshelfTests(unittest.TestCase): 

    @classmethod
    def setUpClass(cls):
        pass 

    @classmethod
    def tearDownClass(cls):
        pass 

    def setUp(self):
        # creates a test client
        self.app = app.test_client()
        # propagate the exceptions to the test client
        self.app.testing = True 

    def tearDown(self):
        pass 

    def test_home_status_code(self):
        # sends HTTP GET request to the application
        # on the specified path
        result = self.app.get('/') 
        # print(result.data)
        # assert the status code of the response
        self.assertEqual(result.status_code, 200) 

    def test_home_data(self):
        # sends HTTP GET request to the application
        # on the specified path
        result = self.app.get('/') 

        # assert the response data
        self.assertTrue("Login Page" in result.data.decode('utf-8'))

    def test_allowed_to_take_test():
        result = allowed_to_take_test("", "")
        self.assertFalse(result)

        # result = allowed_to_take_test("", "sirimala.sreenath@gmail.com")
        # self.assertFalse(result)

        # result = allowed_to_take_test("English Literacy Test", "sirimala.sreenath@gmail.com")
        # self.assertTrue(result)

# runs the unit tests in the module
if __name__ == '__main__':
  unittest.main()
