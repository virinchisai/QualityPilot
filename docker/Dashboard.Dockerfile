FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY qualitypilot qualitypilot
COPY app app
RUN pip install --no-cache-dir '.[dashboard]'
RUN useradd --create-home qualitypilot && chown -R qualitypilot:qualitypilot /app
USER qualitypilot
EXPOSE 8501
CMD ["streamlit", "run", "app/dashboard/main.py", "--server.address=0.0.0.0"]

