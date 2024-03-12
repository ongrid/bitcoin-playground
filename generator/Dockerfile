FROM python:3.12-bullseye
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "/app/generator.py"]
