# Use your custom Python base image
FROM docker.ellisbs.co.uk:5190/python:3.13

# Create a non-root user and group
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Give ownership of the workdir to the new user
RUN chown appuser:appuser /app

# Switch to non-root user
USER appuser

# Copy only the necessary files *after* switching to the user
COPY --chown=appuser:appuser requirements.txt ./
COPY --chown=appuser:appuser vboxmanagemetrics.py ./

# Install dependencies as the appuser (assumes venv or user-site-packages ok)
RUN pip install --no-cache-dir --user -r requirements.txt

# Optional: expose port
EXPOSE 9200

# Run the app with the user's Python binary
CMD ["python", "vboxmanagemetrics.py"]
