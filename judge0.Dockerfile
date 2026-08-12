FROM judge0/judge0:1.13.1

# Install Python 3.11 build dependencies and compile Python 3.11.9
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libgdbm-dev \
    libncurses5-dev \
    libnss3-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    zlib1g-dev \
    wget \
    && cd /tmp \
    && wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tar.xz \
    && tar -xf Python-3.11.9.tar.xz \
    && cd Python-3.11.9 \
    && ./configure --prefix=/usr/local/python-3.11.9 --enable-optimizations \
    && make -j$(nproc) \
    && make altinstall \
    && rm -rf /tmp/Python-3.11.9* \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install required packages (pytest + allowlisted course dependencies) into Python 3.11.9
RUN /usr/local/python-3.11.9/bin/python3.11 -m pip install --no-cache-dir --upgrade pip setuptools \
    && /usr/local/python-3.11.9/bin/python3.11 -m pip install --no-cache-dir \
    pytest \
    pillow \
    pygame \
    tabulate
