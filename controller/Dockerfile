# Grab Python 3.x image
FROM python:3

# Let Python output be sent to the host computer
ENV PYTHONUNBUFFERED 1

# Define/create a working directory for the RUN/CMD/COPY commands
WORKDIR /app

# Copy the requirements for pip into the container
COPY ./src/requirements.txt /app/requirements.txt

# Install the required dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the UDP ports used by the drone
EXPOSE 8889
EXPOSE 8890

# Start the drone command dispatcher
CMD ["python", "command-dispatcher.py"]
