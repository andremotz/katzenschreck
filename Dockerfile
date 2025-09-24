FROM python:3.10

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and MariaDB
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libmariadb-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY cat_detector/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files and modules
COPY cat_detector/ ./cat_detector/
COPY config.txt.example .
COPY database_setup.sql .

# Create output directory
RUN mkdir -p /app/results

# Set executable permissions for start script if needed
# Note: start_script.sh is not included as it's meant for host setup

# Set default working directory to cat_detector
WORKDIR /app/cat_detector

# Create config.txt from example if it doesn't exist
RUN if [ ! -f ../config.txt ]; then cp ../config.txt.example ../config.txt; fi

ENTRYPOINT ["python", "main.py"]
CMD ["/app/results"]