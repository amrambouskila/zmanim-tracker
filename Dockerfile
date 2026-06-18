FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv pip install --system --no-cache -r pyproject.toml

COPY . .

EXPOSE 5270

CMD ["streamlit", "run", "src/app.py", "--server.port=5270", "--server.address=0.0.0.0", "--server.headless=true"]