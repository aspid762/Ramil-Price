import unittest
import json
from app import app

class FlaskTestCase(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_home_status_code(self):
        result = self.app.get('/')
        self.assertEqual(result.status_code, 200)
    
    def test_health_endpoint(self):
        result = self.app.get('/health')
        data = json.loads(result.data)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(data['status'], 'ok')
        self.assertIn('timestamp', data)
    
    def test_info_endpoint(self):
        result = self.app.get('/info')
        data = json.loads(result.data)
        self.assertEqual(result.status_code, 200)
        self.assertIn('app_name', data)
        self.assertIn('version', data)
        self.assertIn('python_version', data)

if __name__ == '__main__':
    unittest.main() 