FROM judge0/judge0:1.13.1

# Base image defaults to non-root user `judge0`; root is required for apt/make install.
USER root

# Judge0 1.13.1 is Debian Buster (EOL). Point apt at archive mirrors and drop
# unrelated third-party repos that are not needed to compile Python 3.11.9.
RUN sed -i 's|deb.debian.org|archive.debian.org|g; s|security.debian.org|archive.debian.org|g' /etc/apt/sources.list \
    && printf 'Acquire::Check-Valid-Until "false";\n' > /etc/apt/apt.conf.d/99no-check-valid-until \
    && rm -f /etc/apt/sources.list.d/mono-official-stable.list /etc/apt/sources.list.d/nodesource.list

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
    && ./configure --prefix=/usr/local/python-3.11.9 \
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
