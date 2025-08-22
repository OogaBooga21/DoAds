# Use an official Python image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- This is the critical part for Playwright ---
# It installs the Chromium browser and its system dependencies
RUN apt-get update && apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libx11-6 libxcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2
RUN playwright install chromium

# Copy all your project files into the container
COPY . .

# Tell the container to expose port 10000 for web traffic
EXPOSE 10000

# The command to run your web app when the container starts
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "240", "app:app"]