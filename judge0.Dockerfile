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
    cmake \
    ca-certificates \
    libffi-dev \
    libgdbm-dev \
    libncurses5-dev \
    libnss3-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    xz-utils \
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

# Install pinned packages (pytest + allowlisted course dependencies) into Python 3.11.9
RUN /usr/local/python-3.11.9/bin/python3.11 -m pip install --no-cache-dir --upgrade pip==24.3.1 setuptools==75.8.0 \
    && /usr/local/python-3.11.9/bin/python3.11 -m pip install --no-cache-dir \
    pytest==8.4.2 \
    pillow==11.3.0 \
    pygame==2.6.1 \
    tabulate==0.9.0

# CMake 3.28.3 (checksum-pinned) required to configure GoogleTest 1.17.0+
ARG CMAKE_VERSION=3.28.3
ARG CMAKE_SHA256=804d231460ab3c8b556a42d2660af4ac7a0e21c98a7f8ee3318a74b4a9a187a6
RUN cd /tmp \
    && wget -O cmake.tar.gz "https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz" \
    && echo "${CMAKE_SHA256}  cmake.tar.gz" | sha256sum -c - \
    && tar -xzf cmake.tar.gz --strip-components=1 -C /usr/local \
    && rm -f cmake.tar.gz

# GoogleTest 1.17.0 (checksum-pinned) for native unit-test grading.
ARG GTEST_VERSION=1.17.0
ARG GTEST_SHA256=65fab701d9829d38cb77c14acdc431d2108bfdbf8979e40eb8ae567edf10b27c
RUN cd /tmp \
    && wget -O googletest.tar.gz "https://github.com/google/googletest/archive/refs/tags/v${GTEST_VERSION}.tar.gz" \
    && echo "${GTEST_SHA256}  googletest.tar.gz" | sha256sum -c - \
    && tar -xzf googletest.tar.gz \
    && cmake -S "googletest-${GTEST_VERSION}" -B gtest-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DBUILD_GMOCK=OFF \
        -DINSTALL_GTEST=ON \
    && cmake --build gtest-build -j"$(nproc)" \
    && cmake --install gtest-build \
    && rm -rf /tmp/googletest.tar.gz /tmp/googletest-${GTEST_VERSION} /tmp/gtest-build

# Node 24.22.3 (checksum-pinned) plus locked jsdom/esbuild for Web grading.
ARG NODE_VERSION=24.22.3
ARG NODE_SHA256=4f2b175a6d53a5c617a80dba2676238a0688cef28c6da4eba35c7d844e66fcfb
ARG JSDOM_VERSION=29.1.1
ARG ESBUILD_VERSION=0.28.2
RUN cd /tmp \
    && wget -O node.tar.xz "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
    && echo "${NODE_SHA256}  node.tar.xz" | sha256sum -c - \
    && mkdir -p /opt/autograder \
    && tar -xJf node.tar.xz -C /opt/autograder \
    && mv "/opt/autograder/node-v${NODE_VERSION}-linux-x64" /opt/autograder/node \
    && mkdir -p /opt/autograder/web \
    && cd /opt/autograder/web \
    && export PATH="/opt/autograder/node/bin:$PATH" \
    && npm init -y \
    && npm install --omit=dev --no-fund --no-audit \
        "jsdom@${JSDOM_VERSION}" \
        "esbuild@${ESBUILD_VERSION}" \
    && node -e "require('jsdom'); require('esbuild')" \
    && rm -rf /tmp/node.tar.xz /root/.npm

USER judge0
