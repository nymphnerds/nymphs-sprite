#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_sprite_foundry_common.sh"

module_version="$(sprite_foundry_version_from_manifest "${REPO_DIR}/nymph.json")"
install_parent="$(dirname "${SPRITE_FOUNDRY_INSTALL_DIR}")"
mkdir -p "${install_parent}"
staging_dir="$(mktemp -d "${install_parent}/.nymphs-sprite-install.XXXXXX")"
cleanup() {
  rm -rf "${staging_dir}"
}
trap cleanup EXIT

echo "Installing ${SPRITE_FOUNDRY_MODULE_NAME} ${module_version}..."
echo "install_root=${SPRITE_FOUNDRY_INSTALL_DIR}"

install -m 644 "${REPO_DIR}/nymph.json" "${staging_dir}/nymph.json"
install -m 644 "${REPO_DIR}/README.md" "${staging_dir}/README.md"
install -m 644 "${REPO_DIR}/CHANGELOG.md" "${staging_dir}/CHANGELOG.md"
install -m 644 "${REPO_DIR}/LICENSE" "${staging_dir}/LICENSE"

mkdir -p "${staging_dir}/foundry" "${staging_dir}/pipeline" "${staging_dir}/scripts" "${staging_dir}/ui" "${staging_dir}/docs"
cp -a "${REPO_DIR}/foundry/." "${staging_dir}/foundry/"
cp -a "${REPO_DIR}/pipeline/." "${staging_dir}/pipeline/"
install -m 755 "${REPO_DIR}/scripts/"*.sh "${staging_dir}/scripts/"
if compgen -G "${REPO_DIR}/scripts/*.py" > /dev/null; then
  install -m 755 "${REPO_DIR}/scripts/"*.py "${staging_dir}/scripts/"
fi
if compgen -G "${REPO_DIR}/ui/*.html" > /dev/null; then
  install -m 644 "${REPO_DIR}/ui/"*.html "${staging_dir}/ui/"
fi
if compgen -G "${REPO_DIR}/ui/*.png" > /dev/null; then
  install -m 644 "${REPO_DIR}/ui/"*.png "${staging_dir}/ui/"
fi
if compgen -G "${REPO_DIR}/docs/*.md" > /dev/null; then
  install -m 644 "${REPO_DIR}/docs/"*.md "${staging_dir}/docs/"
fi

sprite_foundry_ensure_dirs

rm -rf "${SPRITE_FOUNDRY_INSTALL_DIR}"
mv "${staging_dir}" "${SPRITE_FOUNDRY_INSTALL_DIR}"
trap - EXIT

printf '%s\n' "${module_version}" > "${SPRITE_FOUNDRY_MARKER_FILE}"
sprite_foundry_touch_log
{
  printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'installed_module_version=%s\n' "${module_version}"
  printf 'install_root=%s\n' "${SPRITE_FOUNDRY_INSTALL_DIR}"
  printf 'zimage_url=%s\n' "${SPRITE_FOUNDRY_ZIMAGE_URL}"
  printf 'outputs_root=%s\n' "${SPRITE_FOUNDRY_OUTPUTS_ROOT}"
} >> "${SPRITE_FOUNDRY_LOG_FILE}"

echo "installed_module_version=${module_version}"
echo "${SPRITE_FOUNDRY_MODULE_NAME} installed."
