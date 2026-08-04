# Base image
FROM python:3.11.4

# Set working directory
WORKDIR /app

# Install tzdata and set Sydney timezone
RUN apt-get update && apt-get install -y tzdata --no-install-recommends \
    && ln -sf /usr/share/zoneinfo/Australia/Sydney /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "app/main.py"]
