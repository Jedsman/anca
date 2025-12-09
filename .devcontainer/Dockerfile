FROM python:3.13-slim

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Configure apt and install packages
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
    # Common utilities
    git \
    curl \
    wget \
    ca-certificates \
    # Build tools for Python packages
    gcc \
    g++ \
    make \
    # Additional useful tools
    vim \
    nano \
    less \
    # Clean up
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Set up Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create workspace directory
WORKDIR /workspace

# Install common Python development tools
RUN pip install --upgrade pip setuptools wheel

# Create directory for bash history
RUN mkdir -p /commandhistory \
    && touch /commandhistory/.bash_history

# Set up bash history
RUN echo "export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" >> /root/.bashrc

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog

# Default command
CMD ["sleep", "infinity"]
