#!/usr/bin/env python3

from flask import Flask, Response, jsonify
import subprocess
import socket
import argparse

app = Flask(__name__)

# Get hostname for labels
HOSTNAME = socket.gethostname()

def get_metrics():
    metrics = []
    
    # List of metrics to collect - add more as needed
    metric_groups = [
        "Guest/CPU/Load/User:avg",
        "Guest/CPU/Load/System:avg",
        "Guest/CPU/Load/Idle:avg",
        "Guest/RAM/Usage/Used:avg",
        "Guest/RAM/Usage/Free:avg",
        "Host/CPU/Load:avg",
        "Host/RAM/Usage/Used:avg",
        "Host/RAM/Usage/Free:avg",
        "Guest/Network/Rate/Rx:avg",
        "Guest/Network/Rate/Tx:avg"
    ]
    
    # Get VM info first to add better labels
    try:
        vm_info = {}
        vms_output = subprocess.check_output(["VBoxManage", "list", "vms"], 
                                          stderr=subprocess.DEVNULL).decode()
        for line in vms_output.strip().split('\n'):
            if '"' in line and '{' in line:
                name = line.split('"')[1]
                uuid = line.split('{')[1].split('}')[0]
                vm_info[name] = uuid
                
        # Add host metric
        metrics.append(f'vbox_info{{hostname="{HOSTNAME}"}} 1')
    
        # Get metrics for each group
        for metric_group in metric_groups:
            try:
                output = subprocess.check_output([
                    "VBoxManage", "metrics", "query", "*", metric_group
                ], stderr=subprocess.DEVNULL).decode()
                
                lines = output.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 3:
                        vm = parts[0]
                        metric = parts[1]
                        value = parts[2]
                        
                        # Handle different metric formats (%, KB, B/s, etc.)
                        if value.endswith('%'):
                            value = float(value.strip('%'))
                        elif value.endswith('MB'):
                            value = float(value.strip('MB')) * 1024 * 1024
                        elif value.endswith('KB'):
                            value = float(value.strip('KB')) * 1024
                        elif value.endswith('B/s'):
                            value = float(value.strip('B/s'))
                        else:
                            try:
                                value = float(value)
                            except ValueError:
                                continue
                        
                        # Format the metric name for Prometheus
                        metric_name = metric.lower().replace('/', '_').replace(':', '')
                        # Get VM UUID if possible
                        uuid = vm_info.get(vm, "unknown")
                        
                        # Add formatted metric
                        metrics.append(f'vbox_{metric_name}{{vm="{vm}", vm_uuid="{uuid}", host="{HOSTNAME}"}} {value}')
            except subprocess.CalledProcessError:
                # Skip if this metric group fails
                continue
    
    except subprocess.CalledProcessError:
        return "# Error fetching VBox metrics\n"
    
    return '\n'.join(metrics) + '\n'

@app.route('/')
def index():
    response = {
        "name": "vbox-metrics-exporter",
        "description": "Exports VirtualBox VM metrics in Prometheus format",
        "version": "0.2.0",
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
