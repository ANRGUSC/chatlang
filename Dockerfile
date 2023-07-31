# Use an official Python runtime as a parent image
FROM python:3.10.11

# Set the working directory to /app
WORKDIR /app

ADD ./requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
ADD . /app

# Make port 80 available to the world outside this container
EXPOSE 80

# Run gunicorn when the container launches
CMD ["gunicorn", "server:app", "-b", "0.0.0.0:80"]