FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY app ./app
RUN python src/generate_data.py --output /tmp/training.csv --rows 240 --seed 42 &&     python src/evaluate.py --data /tmp/training.csv --model-output models/model.joblib --metrics-output /tmp/metrics.json --minimum-macro-f1 0.80 &&     useradd --uid 10001 --no-create-home appuser
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
