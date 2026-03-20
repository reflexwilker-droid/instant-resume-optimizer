# Start from a pre-made Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy your project files into the container
COPY . .

# Install all the necessary libraries for your project
RUN pip install -r requirements.txt

# Tell the container how to start your app - CHANGED to app.py
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT
