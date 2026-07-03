#!/usr/bin/env bash
set -euo pipefail

KATA_VERSION="${KATA_VERSION:-latest}"
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

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

echo "Installing dependencies..."
apt-get update
apt-get install -y curl ca-certificates tar zstd python3

if [ -n "${KATA_RELEASE_URL:-}" ]; then
  release_url="${KATA_RELEASE_URL}"
else
  echo "Resolving latest Kata Containers static asset for ${kata_arch}..."
  release_url="$(python3 - "${kata_arch}" "${KATA_VERSION}" <<'PY'
import json
import sys
import urllib.request

arch = sys.argv[1]
version = sys.argv[2]
if version == "latest":
    api_url = "https://api.github.com/repos/kata-containers/kata-containers/releases/latest"
else:
    api_url = f"https://api.github.com/repos/kata-containers/kata-containers/releases/tags/{version}"

with urllib.request.urlopen(api_url) as response:
    release = json.load(response)

for asset in release.get("assets", []):
    name = asset.get("name", "")
    if name.startswith("kata-static-") and arch in name and name.endswith(".tar.zst"):
        print(asset["browser_download_url"])
        break
else:
    raise SystemExit(f"Could not find kata-static asset for {arch} in latest Kata release.")
PY
)"
fi

echo "Downloading Kata Containers from ${release_url}..."
curl -fL "${release_url}" -o "${tmp_dir}/kata-static.tar.zst"

echo "Installing Kata static payload into /opt/kata..."
tar --zstd -xf "${tmp_dir}/kata-static.tar.zst" -C /

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
