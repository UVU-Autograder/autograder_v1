#!/usr/bin/env bash
set -euo pipefail

KATA_VERSION="${KATA_VERSION:-3.32.0}"
KATA_RUNTIME_NAME="${KATA_RUNTIME_NAME:-kata-runtime}"
KATA_INSTALL_DIR="${KATA_INSTALL_DIR:-/opt/kata}"

if [ "${EUID}" -ne 0 ]; then
  echo "Run with sudo: sudo $0" >&2
  exit 1
fi

case "$(uname -m)" in
  x86_64 | amd64)
    kata_arch="amd64"
    ;;
  aarch64 | arm64)
    kata_arch="arm64"
    ;;
  *)
    echo "Unsupported architecture: $(uname -m)" >&2
    exit 1
    ;;
esac

if [ ! -e /dev/kvm ]; then
  cat >&2 <<'EOF'
/dev/kvm was not found. Kata needs hardware virtualization exposed to this host.
Enable virtualization in BIOS/UEFI, or enable nested virtualization if this is a VM.
EOF
  exit 1
fi

release_url="${KATA_RELEASE_URL:-https://github.com/kata-containers/kata-containers/releases/download/${KATA_VERSION}/kata-static-${KATA_VERSION}-${kata_arch}.tar.xz}"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

echo "Installing dependencies..."
apt-get update
apt-get install -y curl ca-certificates tar xz-utils python3

echo "Downloading Kata Containers ${KATA_VERSION} for ${kata_arch}..."
curl -fL "${release_url}" -o "${tmp_dir}/kata-static.tar.xz"

echo "Installing Kata static payload into /opt/kata..."
tar -xJf "${tmp_dir}/kata-static.tar.xz" -C /

if [ ! -x "${KATA_INSTALL_DIR}/bin/kata-runtime" ]; then
  echo "kata-runtime was not found at ${KATA_INSTALL_DIR}/bin/kata-runtime after extraction." >&2
  echo "If the release asset layout changed, find the current kata-static asset URL and rerun with:" >&2
  echo "  sudo KATA_RELEASE_URL=<asset-url> $0" >&2
  exit 1
fi

ln -sf "${KATA_INSTALL_DIR}/bin/kata-runtime" /usr/local/bin/kata-runtime

mkdir -p /etc/docker
if [ ! -f /etc/docker/daemon.json ]; then
  printf '{}\n' >/etc/docker/daemon.json
fi

echo "Registering Docker runtime ${KATA_RUNTIME_NAME}..."
python3 - <<PY
import json
from pathlib import Path

path = Path("/etc/docker/daemon.json")
data = json.loads(path.read_text() or "{}")
data.setdefault("runtimes", {})["${KATA_RUNTIME_NAME}"] = {
    "path": "${KATA_INSTALL_DIR}/bin/kata-runtime"
}
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY

systemctl restart docker

echo "Docker runtimes:"
docker info --format '{{json .Runtimes}}'

echo "Testing Kata runtime with busybox..."
docker run --rm --runtime "${KATA_RUNTIME_NAME}" busybox uname -a

cat <<EOF

Kata is registered as Docker runtime: ${KATA_RUNTIME_NAME}

Start the autograder POC with the optional Kata compose override:

  docker compose --env-file .env.local \\
    -f docker-compose.poc.yml \\
    -f docker-compose.kata.yml \\
    up --build

EOF
