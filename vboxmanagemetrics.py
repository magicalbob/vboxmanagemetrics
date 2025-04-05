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
        
        # Get VM info for better labels
        vm_info = get_vm_info()
        
        # Get all metrics at once for efficiency
        output = subprocess.check_output(["VBoxManage", "metrics", "query", "*"], 
                                      stderr=subprocess.DEVNULL).decode()
        
        # Process each line of output
        lines = output.strip().split('\n')
        for line in lines:
            parts = line.split(None, 2)  # Split into max 3 parts
            if len(parts) == 3:
                object_name, metric_name, value_str = parts
                
                # Parse value into appropriate numeric type
                value = parse_value(value_str)
                if value is None:
                    continue  # Skip if value couldn't be parsed
                
                # Generate appropriate labels
                labels = {}
                
                if object_name == "host":
                    # Host metrics
                    labels["host"] = HOSTNAME
                    
                    # Handle special cases for network interfaces
                    if metric_name.startswith("Net/"):
                        interface = metric_name.split("/")[1]
                        labels["interface"] = interface
                        metric_type = "/".join(metric_name.split("/")[2:])
                        metric_name = f"host_net_{normalize_metric_name(metric_type)}"
                    # Handle special cases for disk metrics
                    elif metric_name.startswith("Disk/"):
                        disk = metric_name.split("/")[1]
                        labels["disk"] = disk
                        metric_type = "/".join(metric_name.split("/")[2:])
                        metric_name = f"host_disk_{normalize_metric_name(metric_type)}"
                    # Handle special cases for filesystem metrics
                    elif metric_name.startswith("FS/"):
                        fs = metric_name.split("/")[1].replace("{", "").replace("}", "")
                        labels["filesystem"] = fs
                        metric_type = "/".join(metric_name.split("/")[3:])
                        metric_name = f"host_fs_{normalize_metric_name(metric_type)}"
                    else:
                        # Regular host metrics
                        metric_name = f"host_{normalize_metric_name(metric_name)}"
                else:
                    # VM metrics
                    labels["vm"] = object_name
                    labels["host"] = HOSTNAME
                    
                    # Add UUID if available
                    if object_name in vm_info:
                        labels["vm_uuid"] = vm_info[object_name]
                    
                    metric_name = f"guest_{normalize_metric_name(metric_name)}"
                
                # Format labels for Prometheus
                labels_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
                
                # Add formatted metric
                metrics.append(f'vbox_{metric_name}{{{labels_str}}} {value}')
    
    except subprocess.CalledProcessError as e:
        return f"# Error fetching VBox metrics: {str(e)}\n"
    
    return '\n'.join(metrics) + '\n'

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
