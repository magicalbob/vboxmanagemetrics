#!/usr/bin/env python3

import pytest
import os
import sys

# Add parent directory to path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_vbox_list_output():
    """Sample output from VBoxManage list vms command"""
    return """
"t7610_cluster2_node1_1733564785143_85289" {6b0c9a26-25e7-42cb-9857-8d3ad2c8cdb0}
"t7610_cluster2_node2_1733564912253_18594" {e0f9f1f0-8dc9-4ef2-ba99-d7c3e5731e90}
"t7610_cluster2_node3_1733564972679_41652" {f8de6f8d-8faa-4e9a-8b5f-8d15a8e7a90c}
"test_pm1_1743755266192_18850" {39bb65b6-4c39-4e63-a1d1-0a6a76d3b9a7}
    """

@pytest.fixture
def mock_vbox_metrics_output():
    """Sample output from VBoxManage metrics query command"""
    return """
Object      Metric                                 Value
host        CPU/Load/User                          1.56%
host        CPU/Load/Kernel                        12.98%
host        CPU/Load/Idle                          85.45%
host        RAM/Usage/Total                        263535524 kB
host        RAM/Usage/Used                         133893824 kB
host        RAM/Usage/Free                         129641700 kB
host        Disk/sdc/Load/Util                     1.45%
host        Disk/sdc/Usage/Total                   457862 MB
host        Net/enp0s25/LinkSpeed                  1000 mbit/s
host        Net/enp0s25/Load/Rx                    0.00%
host        Net/enp0s25/Load/Tx                    0.00%
host        FS/{/}/Usage/Total                     71645 MB
host        FS/{/}/Usage/Used                      67770 MB
host        FS/{/}/Usage/Free                      3874 MB
t7610_cluster2_node1_1733564785143_85289 CPU/Load/User                          3.0%
t7610_cluster2_node2_1733564912253_18594 CPU/Load/User                          0.0%
test_pm1_1743755266192_18850 CPU/Load/User                          38.0%
t7610_cluster2_node1_1733564785143_85289 RAM/Usage/Total                        4096000 kB
t7610_cluster2_node1_1733564785143_85289 RAM/Usage/Used                         2048000 kB
t7610_cluster2_node1_1733564785143_85289 RAM/Usage/Free                         2048000 kB
    """

@pytest.fixture
def app_client():
    """Fixture for Flask test client"""
    import vboxmanagemetrics
    vboxmanagemetrics.app.testing = True
    return vboxmanagemetrics.app.test_client()
