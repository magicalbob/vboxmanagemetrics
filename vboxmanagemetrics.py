#!/usr/bin/env python3

from flask import Flask, Response, jsonify
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

@app.route('/')
def index():
    response = {
        "name": "vbox-metrics-exporter",
        "description": "Exports VirtualBox VM metrics in Prometheus format",
        "version": "0.1.0",
        "author": "ellisbs",
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
