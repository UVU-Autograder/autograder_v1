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

shim_binary=""
if [ -x "${KATA_INSTALL_DIR}/runtime-rs/bin/containerd-shim-kata-v2" ]; then
  shim_binary="${KATA_INSTALL_DIR}/runtime-rs/bin/containerd-shim-kata-v2"
elif [ -x "${KATA_INSTALL_DIR}/bin/containerd-shim-kata-v2" ]; then
  shim_binary="${KATA_INSTALL_DIR}/bin/containerd-shim-kata-v2"
else
  echo "containerd-shim-kata-v2 was not found under ${KATA_INSTALL_DIR} after extraction." >&2
  echo "If the release asset layout changed, find the current kata-static asset URL and rerun with:" >&2
  echo "  sudo KATA_RELEASE_URL=<asset-url> $0" >&2
  exit 1
fi

ln -sf "${shim_binary}" /usr/local/bin/containerd-shim-kata-v2
ln -sf "${shim_binary}" /usr/bin/containerd-shim-kata-v2
if [ -x "${KATA_INSTALL_DIR}/bin/kata-runtime" ]; then
  ln -sf "${KATA_INSTALL_DIR}/bin/kata-runtime" /usr/local/bin/kata-runtime
fi

# runtime-rs reads /etc/kata-containers/runtime-rs/configuration.toml -- NOT the
# /etc/kata-containers/configuration.toml path used by the (deprecated) Go runtime.
# Writing to the wrong path is silently ignored; verify with:
#   journalctl -u containerd | grep "load configuration from"
KATA_ETC_DIR="/etc/kata-containers"
if [ -n "${shim_binary##*runtime-rs*}" ]; then
  kata_default_config="${KATA_INSTALL_DIR}/share/defaults/kata-containers/configuration.toml"
  kata_etc_config="${KATA_ETC_DIR}/configuration.toml"
else
  kata_default_config="${KATA_INSTALL_DIR}/share/defaults/kata-containers/runtime-rs/configuration-qemu-runtime-rs.toml"
  kata_etc_config="${KATA_ETC_DIR}/runtime-rs/configuration.toml"
  KATA_ETC_DIR="${KATA_ETC_DIR}/runtime-rs"
fi

mkdir -p "${KATA_ETC_DIR}"
if [ -f "${kata_default_config}" ] && [ ! -f "${kata_etc_config}" ]; then
  echo "Installing editable Kata config at ${kata_etc_config}..."
  cp "${kata_default_config}" "${kata_etc_config}"
elif [ ! -f "${kata_default_config}" ]; then
  echo "WARNING: expected default config not found at ${kata_default_config}." >&2
  echo "Kata will run from its built-in defaults; host tuning will have no effect." >&2
fi

# NOTE: privileged_without_host_devices is deliberately NOT set here.
# It is a containerd-CRI / CRI-O runtime option and has no equivalent under
# standalone Docker Engine -- it is not a field in Kata's own config schema and
# is silently discarded if written to configuration.toml. Judge0 runs under Kata
# via a bounded capability set instead of --privileged; see docker-compose.kata.yml.

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
    "runtimeType": "io.containerd.kata.v2"
}
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY

systemctl restart docker

echo "Docker runtimes:"
docker info --format '{{json .Runtimes}}'

echo "Testing Kata runtime with busybox..."
docker run --rm --runtime "${KATA_RUNTIME_NAME}" busybox uname -a

echo ""
echo "Verifying the config file Kata actually loads..."
loaded_config="$(journalctl -u containerd --since '1 minute ago' --no-pager 2>/dev/null \
  | grep -o 'load configuration from: .*' | tail -1)"
if [ -n "${loaded_config}" ]; then
  echo "  ${loaded_config}"
  case "${loaded_config}" in
    *"${kata_etc_config}"*)
      echo "OK: host tuning in ${kata_etc_config} is being honored."
      ;;
    *)
      echo "WARNING: Kata is loading its built-in defaults, not ${kata_etc_config}." >&2
      echo "Any vCPU/memory/hugepage tuning placed there will silently do nothing." >&2
      ;;
  esac
else
  echo "  (no 'load configuration' line found; check journalctl -u containerd manually)"
fi

echo ""
echo "Verifying Judge0's capability set works under Kata (no --privileged)..."
if docker run --rm \
  --cap-add SYS_ADMIN --cap-add SYS_RESOURCE --cap-add SYS_CHROOT \
  --cap-add SETUID --cap-add SETGID --cap-add DAC_OVERRIDE --cap-add MKNOD \
  --runtime "${KATA_RUNTIME_NAME}" busybox true; then
  echo "OK: capability-based container starts under Kata."
else
  cat >&2 <<'EOF'

WARNING: A capability-scoped container failed to start under Kata. Judge0 needs
this to work, since running it with --privileged makes Kata attempt to hot-plug
every host /dev entry into the guest, which fails with:
  "get host path failed / No such file or directory (os error 2)"
EOF
fi

cat <<EOF

Kata is registered as Docker runtime: ${KATA_RUNTIME_NAME}

Start the autograder with the Kata compose override:

  docker compose --env-file .env.local \
    -f docker-compose.yml \
    -f docker-compose.kata.yml \
    up -d --build

EOF
