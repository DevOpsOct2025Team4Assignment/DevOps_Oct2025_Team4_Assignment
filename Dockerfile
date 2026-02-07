FROM python:3.12-slim

WORKDIR /file-manager

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:create_app()"]