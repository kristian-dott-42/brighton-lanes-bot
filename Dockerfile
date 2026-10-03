FROM python:3.13-slim

# Print output goes straight to `docker logs`
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY brighton_botv2.py .

# The bot reads praw.ini and replied_to.txt from its working directory
WORKDIR /data
CMD ["python", "/app/brighton_botv2.py"]
