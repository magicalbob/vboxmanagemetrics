# Use a lightweight Python base image
FROM docker.ellisbs.co.uk:5190/python:3.13

# Set workdir inside container
WORKDIR /app

# Install system dependencies if needed (e.g., VBoxManage if desired — see below)

# Copy only the necessary files
COPY vboxmanagemetrics.py ./
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Optional: expose the port if it's a Flask server
EXPOSE 9200

# Define default command to run the script
CMD ["python", "vboxmanagemetrics.py"]
