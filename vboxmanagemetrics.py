#!/usr/bin/env python3

from flask import Flask, Response
import subprocess
import argparse

app = Flask(__name__)

def get_metrics():
    try:
        output = subprocess.check_output([
            "VBoxManage", "metrics", "query", "*", "Guest/CPU/Load/User:avg"
        ], stderr=subprocess.DEVNULL).decode()

        lines = output.strip().split('\n')
        metrics = []
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) == 3:
                vm, metric, value = parts
                # Remove percent symbol and convert to float
                try:
                    value = float(value.strip('%'))
                    metric_name = metric.lower().replace('/', '_').replace(':', '')
                    metrics.append(f'vbox_{metric_name}{{vm="{vm}"}} {value}')
                except ValueError:
                    continue

        return '\n'.join(metrics) + '\n'
    except subprocess.CalledProcessError:
        return "# Error fetching VBox metrics\n"

@app.route('/metrics')
def metrics():
    return Response(get_metrics(), mimetype='text/plain')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='VirtualBox Prometheus Exporter')
    parser.add_argument('--port', type=int, default=9200, help='Port to serve metrics on')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port)
