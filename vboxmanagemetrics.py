#!/usr/bin/env python3

from flask import Flask, Response, jsonify
import subprocess
import socket
import re
import argparse

app = Flask(__name__)

# Get hostname for labels
HOSTNAME = socket.gethostname()

def normalize_metric_name(metric_name):
    """Convert VBox metric name to Prometheus format"""
    # Replace special characters and convert to lowercase
    name = metric_name.lower().replace('/', '_').replace(':', '_')
    # Remove parentheses and replace with underscores
    name = re.sub(r'[{}()]', '_', name)
    # Replace multiple underscores with a single one
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    return name.strip('_')

def parse_value(value_str):
    """Parse different value formats into numeric values"""
    if value_str.endswith('%'):
        return float(value_str.strip('%'))
    elif value_str.endswith('MB'):
        return float(value_str.strip('MB')) * 1024 * 1024
    elif value_str.endswith('kB'):
        return float(value_str.strip('kB')) * 1024
    elif value_str.endswith('B/s'):
        return float(value_str.strip('B/s'))
    elif value_str.endswith('mbit/s'):
        return float(value_str.strip('mbit/s'))
    elif value_str.endswith('MHz'):
        return float(value_str.strip('MHz'))
    else:
        try:
            # Handle "NaN" case specially
            if value_str.lower() == "nan":
                return None
            return float(value_str)
        except ValueError:
            return None

def get_info_metric():
    return f'vbox_info{{hostname="{HOSTNAME}"}} 1'

def get_vm_info():
        # Get VM info for better labels
        vm_info = {}
        vms_output = subprocess.check_output(["VBoxManage", "list", "vms"],
                                          stderr=subprocess.DEVNULL).decode()
        for line in vms_output.strip().split('\n'):
            if '"' in line and '{' in line:
                name = line.split('"')[1]
                uuid = line.split('{')[1].split('}')[0]
                vm_info[name] = uuid

        return vm_info

def get_metrics():
    metrics = []

    try:
        # Add host info metric
        metrics.append(f'vbox_info{{hostname="{HOSTNAME}"}} 1')

        # Fetch VM info for labels
        vm_info = get_vm_info()

        # Fetch all VBox metrics
        output = subprocess.check_output(["VBoxManage", "metrics", "query", "*"], 
                                          stderr=subprocess.DEVNULL).decode()

        # Process metrics output
        for line in output.strip().split('\n'):
            process_metric_line(line, metrics, vm_info)

    except subprocess.CalledProcessError as e:
        return f"# Error fetching VBox metrics: {str(e)}\n"

    return '\n'.join(metrics) + '\n'

def get_vm_info():
    """Fetch VM names and UUIDs from VBoxManage."""
    vm_info = {}
    vms_output = subprocess.check_output(["VBoxManage", "list", "vms"], 
                                         stderr=subprocess.DEVNULL).decode()
    for line in vms_output.strip().split('\n'):
        if '"' in line and '{' in line:
            name = line.split('"')[1]
            uuid = line.split('{')[1].split('}')[0]
            vm_info[name] = uuid
    return vm_info

def process_metric_line(line, metrics, vm_info):
    """Process a single metric line and add it to the metrics list."""
    parts = line.split(None, 2)  # Split into max 3 parts
    if len(parts) != 3:
        return

    object_name, metric_name, value_str = parts
    value = parse_value(value_str)
    if value is None:
        return

    labels = {"host": HOSTNAME}
    metric_prefix = "vbox_"

    if object_name == "host":
        labels = process_host_metric(metric_name, labels)
        metric_name = f"{metric_prefix}host_{normalize_metric_name(metric_name)}"
    else:
        labels = process_vm_metric(object_name, labels, vm_info)
        metric_name = f"{metric_prefix}guest_{normalize_metric_name(metric_name)}"

    labels_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
    metrics.append(f'{metric_name}{{{labels_str}}} {value}')

def process_host_metric(metric_name, labels):
    """Handle special cases for host metrics."""
    if metric_name.startswith("Net/"):
        interface = metric_name.split("/")[1]
        labels["interface"] = interface
        metric_name = f'host_net_{normalize_metric_name("/".join(metric_name.split("/")[2:]))}'
    elif metric_name.startswith("Disk/"):
        disk = metric_name.split("/")[1]
        labels["disk"] = disk
        metric_name = f'host_disk_{normalize_metric_name("/".join(metric_name.split("/")[2:]))}'
    elif metric_name.startswith("FS/"):
        fs = metric_name.split("/")[1].replace("{", "").replace("}", "")
        labels["filesystem"] = fs
        metric_name = f'host_fs_{normalize_metric_name("/".join(metric_name.split("/")[3:]))}'
    return labels

def process_vm_metric(object_name, labels, vm_info):
    """Handle special cases for VM metrics."""
    labels["vm"] = object_name
    if object_name in vm_info:
        labels["vm_uuid"] = vm_info[object_name]
    return labels

@app.route('/')
def index():
    response = {
        "name": "vbox-metrics-exporter",
        "description": "Exports VirtualBox VM metrics in Prometheus format",
        "version": "0.3.0",
        "author": "ellisbs",
        "hostname": HOSTNAME,
        "tagline": "You know, for metrics"
    }
    return app.response_class(
        response=app.json.dumps(response, indent=2) + "\n",
        status=200,
        mimetype='application/json'
    )

@app.route('/metrics')
def metrics():
    return Response(get_metrics(), mimetype='text/plain')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='VirtualBox Prometheus Exporter')
    parser.add_argument('--port', type=int, default=9200, help='Port to serve metrics on')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port)
