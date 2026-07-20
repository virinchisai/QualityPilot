FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY qualitypilot qualitypilot
COPY app app
RUN pip install --no-cache-dir .
RUN useradd --create-home qualitypilot && chown -R qualitypilot:qualitypilot /app
USER qualitypilot
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.demo_app.main:app", "--host", "0.0.0.0", "--port", "8000"]

