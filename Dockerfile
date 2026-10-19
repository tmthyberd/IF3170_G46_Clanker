FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/core/*.py src/core/
COPY src/algorithms/hill_climbing/*.py src/algorithms/hill_climbing/
COPY src/algorithms/simulated_annealing/*.py src/algorithms/simulated_annealing/
COPY src/app/*.py src/app/
COPY src/app/assets/* src/app/assets/

CMD ["python3", "-m", "src.app.app"]
