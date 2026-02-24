# use official python image
From python:3.10-slim

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# set Workdir
WORKDIR /app

# Install OS dependencies
RUN apt-get update && apt-get install -y build-essential poppler-utils && rm -rf /var/lib/apt/lists/*

# copy requiremnets
COPY requiremnets.txt .

COPY .env .

# copy project files
COPY . .

# install dependencies
RUN pip install --no-cache-dir -r requiremnets.txt

# #Expose port
EXPOSE 8080

# RUN FASTAPI with uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

# replace last CMD in prod
#CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]



