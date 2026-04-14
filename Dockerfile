FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv pip install --system --no-cache -r pyproject.toml

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "zmanim_tracker.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]