#!/usr/bin/env python3

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add parent directory to path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import vboxmanagemetrics

class TestFlaskIntegration(unittest.TestCase):
    
    def setUp(self):
        vboxmanagemetrics.app.testing = True
        self.app = vboxmanagemetrics.app.test_client()
        # Mock the hostname
        vboxmanagemetrics.HOSTNAME = "test-host"
    
    def test_index_response_format(self):
        """Test that the index route returns correctly formatted JSON"""
        response = self.app.get('/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check required fields
        self.assertIn('name', data)
        self.assertIn('description', data)
        self.assertIn('version', data)
        self.assertIn('author', data)
        self.assertIn('hostname', data)
        self.assertIn('tagline', data)
        
        # Check values
        self.assertEqual(data['name'], "vbox-metrics-exporter")
        self.assertEqual(data['hostname'], "test-host")
        self.assertEqual(data['author'], "ellisbs")
    
    @patch('vboxmanagemetrics.get_metrics')
    def test_metrics_response_format(self, mock_get_metrics):
        """Test that the metrics route returns correct content type"""
        mock_metrics = """
vbox_info{hostname="test-host"} 1
vbox_host_cpu_load_user{host="test-host"} 1.56
vbox_guest_cpu_load_user{host="test-host",vm="test-vm",vm_uuid="uuid"} 10.5
"""
        mock_get_metrics.return_value = mock_metrics
        
        response = self.app.get('/metrics')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/plain; charset=utf-8')  # Fix: include charset
        self.assertEqual(response.data.decode(), mock_metrics)
    
    @patch('vboxmanagemetrics.get_metrics')
    def test_metrics_error_handling(self, mock_get_metrics):
        """Test that errors in metrics generation are properly handled"""
        error_msg = "# Error fetching VBox metrics: Command failed\n"
        mock_get_metrics.return_value = error_msg
        
        response = self.app.get('/metrics')
        
        self.assertEqual(response.status_code, 200)  # Should still return 200 with error message
        self.assertEqual(response.content_type, 'text/plain; charset=utf-8')  # Fix: include charset
        self.assertEqual(response.data.decode(), error_msg)
    
    def test_nonexistent_route(self):
        """Test that non-existent routes return 404"""
        response = self.app.get('/nonexistent')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
