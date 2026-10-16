# Stage 1: install dependencies into a virtualenv
FROM python:3.12-slim AS build
WORKDIR /build
COPY requirements.txt .
RUN python -m venv /venv && /venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: small runtime image with only the venv and the app code
FROM python:3.12-slim
RUN useradd --uid 10001 --no-create-home pulse
WORKDIR /srv
COPY --from=build /venv /venv
COPY app/ app/
# No .pyc files: the root filesystem is read-only in Kubernetes
ENV PATH="/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER 10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
