# Ultra-optimized Dockerfile for competition submission
FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with maximum optimization
RUN pip install --no-cache-dir --no-compile -r requirements.txt \
    && pip cache purge \
    && rm -rf ~/.cache/pip \
    && find /usr/local -depth \( -name '__pycache__' -o -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf '{}' + \
    && find /usr/local -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local -name "test*" -type d -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local -name "*.so" -exec strip {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.9/site-packages -name "*.so" -exec strip {} + 2>/dev/null || true \
    && rm -rf /usr/local/lib/python3.9/site-packages/*/tests/ \
    && rm -rf /usr/local/lib/python3.9/site-packages/*/test/ \
    && rm -rf /usr/local/lib/python3.9/site-packages/*/__pycache__/ \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && rm -rf /usr/share/doc /usr/share/man /usr/share/info /usr/share/locale \
    && rm -rf /var/cache/apt/* /var/lib/apt/lists/* /var/log/*

# Copy source code
COPY extract_outline.py .
COPY utils/ ./utils/

# Create directories
RUN mkdir -p /app/input /app/output

CMD ["python", "extract_outline.py"]
