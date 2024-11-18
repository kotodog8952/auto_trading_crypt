# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Add current directory contents to the container at /app
# COPY ../../container/structuring/ /opt/ml
COPY ./requirements.txt /opt/ml/
# COPY ../data /opt/ml/data

# Set the working directory in the container
WORKDIR /opt/ml/

# Create a directory
RUN mkdir -p /opt/ml/input /opt/ml/output /opt/ml/utils /opt/ml/code

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
# RUN pip install --no-cache-dir -r requirements.txt
# RUN pip install -r ./requirements.txt

# Make port 80 available to the world outside this container
# EXPOSE 80

# Define environment variable
# ENV NAME World

# Run app.py when the container launches
# CMD ["python", "app.py"]
