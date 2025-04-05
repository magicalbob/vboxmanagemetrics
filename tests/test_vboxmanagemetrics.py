#!/usr/bin/env python3

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
import subprocess  # Add this import

# Add parent directory to path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import vboxmanagemetrics

class TestVBoxMetricsExporter(unittest.TestCase):
    
    def setUp(self):
        self.app = vboxmanagemetrics.app.test_client()
        # Mock the hostname
        vboxmanagemetrics.HOSTNAME = "test-host"
    
    def test_normalize_metric_name(self):
        test_cases = [
            ("CPU/Load/User", "cpu_load_user"),
            ("CPU/Load/User:avg", "cpu_load_user_avg"),
            ("FS/{/}/Usage/Total", "fs_usage_total"),
            ("Net/enp0s25/LinkSpeed", "net_enp0s25_linkspeed"),
            ("RAM/VMM/Ballooned:avg", "ram_vmm_ballooned_avg")
        ]
        
        for input_name, expected_output in test_cases:
            self.assertEqual(vboxmanagemetrics.normalize_metric_name(input_name), expected_output)
    
    def test_parse_value(self):
        test_cases = [
            ("42.5%", 42.5),
            ("100MB", 104857600),  # 100 * 1024 * 1024
            ("1024kB", 1048576),   # 1024 * 1024
            ("500B/s", 500),
            ("100mbit/s", 100),
            ("3400MHz", 3400),
            ("42", 42),
            ("invalid", None)
        ]
        
        for input_str, expected_output in test_cases:
            self.assertEqual(vboxmanagemetrics.parse_value(input_str), expected_output)

    @patch('subprocess.check_output')
    def test_get_metrics_success(self, mock_check_output):
        # Mock the VM list output
        vm_list_output = '"test-vm1" {uuid1}\n"test-vm2" {uuid2}'
        
        # Mock the metrics query output
        metrics_output = (
            "Object      Metric                                 Value\n"
            "host        CPU/Load/User                          1.56%\n"
            "host        RAM/Usage/Used                         4096kB\n"
            "host        Net/eth0/Load/Rx                       5.5%\n"
            "host        Disk/sda/Usage/Total                   100MB\n"
            "host        FS/{/}/Usage/Free                      200MB\n"
            "test-vm1    CPU/Load/User                          10.5%\n"
            "test-vm2    RAM/Usage/Used                         2048kB\n"
        )
        
        # Configure the mock to return different values for different commands
        def side_effect(cmd, stderr=None):
            if cmd[1] == "list":
                return vm_list_output.encode()
            elif cmd[1] == "metrics":
                return metrics_output.encode()
            return b""
        
        mock_check_output.side_effect = side_effect
        
        # Call the function
        metrics = vboxmanagemetrics.get_metrics()
        
        # Verify the output contains expected metrics
        self.assertIn('vbox_info{hostname="test-host"} 1', metrics)
        self.assertIn('vbox_host_cpu_load_user{host="test-host"} 1.56', metrics)
        self.assertIn('vbox_host_ram_usage_used{host="test-host"} 4194304.0', metrics)  # 4096 * 1024
        self.assertIn('vbox_host_net_eth0_load_rx{host="test-host",interface="eth0"} 5.5', metrics)
        self.assertIn('vbox_host_disk_sda_usage_total{host="test-host",disk="sda"} 104857600.0', metrics)
        self.assertIn('vbox_host_fs_usage_free{host="test-host",filesystem=""} 209715200.0', metrics)
        self.assertIn('vbox_guest_cpu_load_user{host="test-host",vm="test-vm1",vm_uuid="uuid1"} 10.5', metrics)
        self.assertIn('vbox_guest_ram_usage_used{host="test-host",vm="test-vm2",vm_uuid="uuid2"} 2097152.0', metrics)  # 2048 * 1024
    
    @patch('subprocess.check_output')
    def test_get_metrics_error(self, mock_check_output):
        # Simulate command failure
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "VBoxManage", b"Error")
        
        # Call the function
        metrics = vboxmanagemetrics.get_metrics()
        
        # Verify we get an error message
        self.assertTrue(metrics.startswith("# Error fetching VBox metrics"))
    
    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        
        # Parse the JSON response
        data = json.loads(response.data)
        self.assertEqual(data['name'], "vbox-metrics-exporter")
        self.assertEqual(data['hostname'], "test-host")
    
    @patch('vboxmanagemetrics.get_metrics')
    def test_metrics_route(self, mock_get_metrics):
        mock_get_metrics.return_value = "mock_metrics_data"
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/plain; charset=utf-8')  # Fix: include charset
        self.assertEqual(response.data.decode(), "mock_metrics_data")

if __name__ == '__main__':
    unittest.main()
