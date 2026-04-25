FROM python:3.11-slim-bookworm

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Prevent Python from writing .pyc files, buffer stdout/stderr, and pin common tooling paths
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/root/.local/bin:${PATH}" \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# In some networks, downloading Playwright browsers from azureedge.net will fail during build.
# Default to skipping browser downloads; enable explicitly if needed.
ARG INSTALL_PLAYWRIGHT_BROWSERS=0

# Install system dependencies required by scientific Python stack, Playwright, Streamlit, and WeasyPrint PDF
RUN <<'EOF'
set -euo pipefail

# Use a mirror to avoid flaky deb.debian.org in some networks
cat >/etc/apt/sources.list <<'EOL'
# Use HTTPS to reduce proxy/ISP tampering with plain HTTP.
deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm main
deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm-updates main
deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main
EOL

apt-get -o Acquire::Retries=8 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 update

if apt-cache show libgdk-pixbuf-2.0-0 >/dev/null 2>&1; then
  GDK_PIXBUF_PKG=libgdk-pixbuf-2.0-0
else
  GDK_PIXBUF_PKG=libgdk-pixbuf2.0-0
fi

apt-get -o Acquire::Retries=8 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 install -y --no-install-recommends \
  build-essential \
  curl \
  git \
  libgl1 \
  libglib2.0-0 \
  libgtk-3-0 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libpangoft2-1.0-0 \
  "${GDK_PIXBUF_PKG}" \
  libffi-dev \
  libcairo2 \
  libatk1.0-0 \
  libatk-bridge2.0-0 \
  libxcb1 \
  libxcomposite1 \
  libxdamage1 \
  libxext6 \
  libxfixes3 \
  libxi6 \
  libxtst6 \
  libnss3 \
  libxrandr2 \
  libxkbcommon0 \
  libasound2 \
  libx11-xcb1 \
  libxshmfence1 \
  libgbm1 \
  ffmpeg

apt-get clean
rm -rf /var/lib/apt/lists/*
EOF

# Install the latest uv release and expose it on PATH
RUN curl -LsSf --retry 3 --retry-delay 2 --proto '=https' --proto-redir '=https' --tlsv1.2 https://astral.sh/uv/install.sh | sh

WORKDIR /app

# Install Python dependencies first to leverage Docker layer caching
COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt

# Install Playwright browser binaries (optional; often blocked by network policies)
RUN if [ "${INSTALL_PLAYWRIGHT_BROWSERS}" = "1" ]; then python -m playwright install chromium; else echo "Skipping Playwright browser download (INSTALL_PLAYWRIGHT_BROWSERS=0)"; fi

# Copy .env
COPY .env.example .env

# Copy application source
COPY . .

# Ensure runtime directories exist even if ignored in build context
RUN mkdir -p /ms-playwright logs final_reports insight_engine_streamlit_reports media_engine_streamlit_reports query_engine_streamlit_reports

EXPOSE 5000 8501 8502 8503

# Default command launches the Flask orchestrator which starts Streamlit agents
CMD ["python", "app.py"]
