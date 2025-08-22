FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./

# Install everything (will install eventlet-0.40.2 due to Ryu)
RUN pip install --no-cache-dir -r requirements.txt

# Force uninstall and reinstall eventlet==0.30.2
RUN pip uninstall -y eventlet && pip install eventlet==0.30.2

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080 6653

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/api/server-stats')"

CMD ["python", "-m", "ryu.cmd.manager", "ryu_lb_basic.py", "--verbose"]
