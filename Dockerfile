# Start from a pre-made Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy your project files into the container
COPY . .

# Install all the necessary libraries for your project
RUN pip install -r requirements.txt

# Tell the container how to start your app
CMD ["python", "resume_optimizer_app.py"]
