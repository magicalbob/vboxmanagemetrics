# VirtualBox Metrics Exporter

This project is a simple Flask application that acts as a metrics exporter for VirtualBox VMs. It retrieves CPU load metrics from VirtualBox Virtual Machines using the `VBoxManage` command and exposes them in a format suitable for Prometheus monitoring.

## Features

- Exports VirtualBox VM metrics in Prometheus format.
- HTTP interface for exposing metrics.
- Basic information about the application available at the root endpoint.

## Prerequisites

- Python 3.x
- VirtualBox with `VBoxManage` command available in your PATH.
- A running Flask environment.

## Installation

1. Clone the repository or download the project files to your local machine.

2. Set up a virtual environment:

   ```bash
   python3 -m venv vboxmanagemetrics_env
   source vboxmanagemetrics_env/bin/activate
   pip install -r requirements.txt
   ```

## Configuration

- Modify the `vboxmanagemetrics.sh` script as necessary.
- Set the user that will run the service in the `systemd/vboxmanagemetrics.service` file.
- Ensure the `WorkingDirectory` points to the correct location of the project.

## Running the Application

You can run the application manually using the following command:

```bash
python3 vboxmanagemetrics.py --port 9200
```

Replace `9200` with any port you want to use.

### Using systemd

To run the application as a systemd service, follow these steps:

1. Copy the `vboxmanagemetrics.service` file to the systemd service directory:

   ```bash
   sudo cp systemd/vboxmanagemetrics.service /etc/systemd/system/
   ```

2. Reload systemd to recognize the new service:

   ```bash
   sudo systemctl daemon-reload
   ```

3. Enable and start the service:

   ```bash
   sudo systemctl enable vboxmanagemetrics.service
   sudo systemctl start vboxmanagemetrics.service
   ```

4. Check the status of the service:

   ```bash
   sudo systemctl status vboxmanagemetrics.service
   ```

## Accessing the Metrics

Once the application is running, you can access the metrics at:

```
http://<your-server-ip>:9200/metrics
```

And basic application information at:

```
http://<your-server-ip>:9200/
```

## Prometheus

Add a target to your prometheis config map something like this:

static_configs:\n      - targets: ['192.168.0.16:9200']\n    metrics_path:
    '/metrics'\n    scheme: http\n    honor_labels: true\n

## Grafana

Dashboard JSON `vboxmanagemetrics.dashboard.json` is included.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for more information.

## Author

- **Name**: Ian Ellis
- **Tagline**: You know, for metrics

Feel free to customize and expand this README file according to your needs!
