#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

module_version="$(nymphs_sprite_version_from_manifest "${REPO_DIR}/nymph.json")"
install_parent="$(dirname "${NYMPHS_SPRITE_INSTALL_DIR}")"
mkdir -p "${install_parent}"
staging_dir="$(mktemp -d "${install_parent}/.nymphs-sprite-install.XXXXXX")"
cleanup() {
  rm -rf "${staging_dir}"
}
trap cleanup EXIT

echo "Installing ${NYMPHS_SPRITE_MODULE_NAME} ${module_version}..."
echo "install_root=${NYMPHS_SPRITE_INSTALL_DIR}"

install -m 644 "${REPO_DIR}/nymph.json" "${staging_dir}/nymph.json"
install -m 644 "${REPO_DIR}/README.md" "${staging_dir}/README.md"
if [[ -f "${REPO_DIR}/CHANGELOG.md" ]]; then
  install -m 644 "${REPO_DIR}/CHANGELOG.md" "${staging_dir}/CHANGELOG.md"
fi
if [[ -f "${REPO_DIR}/THIRD_PARTY_NOTICES.md" ]]; then
  install -m 644 "${REPO_DIR}/THIRD_PARTY_NOTICES.md" "${staging_dir}/THIRD_PARTY_NOTICES.md"
fi

mkdir -p "${staging_dir}/scripts" "${staging_dir}/docs" "${staging_dir}/comfyui_workflows" "${staging_dir}/profiles" "${staging_dir}/ui"
install -m 755 "${REPO_DIR}/scripts/"*.sh "${staging_dir}/scripts/"
install -m 755 "${REPO_DIR}/scripts/"*.py "${staging_dir}/scripts/"
install -m 644 "${REPO_DIR}/docs/"*.md "${staging_dir}/docs/"
install -m 644 "${REPO_DIR}/comfyui_workflows/"*.json "${staging_dir}/comfyui_workflows/"
install -m 644 "${REPO_DIR}/profiles/"*.json "${staging_dir}/profiles/"
install -m 644 "${REPO_DIR}/ui/"*.html "${staging_dir}/ui/"

nymphs_sprite_ensure_dirs

rm -rf "${NYMPHS_SPRITE_INSTALL_DIR}"
mv "${staging_dir}" "${NYMPHS_SPRITE_INSTALL_DIR}"
trap - EXIT

printf '%s\n' "${module_version}" > "${NYMPHS_SPRITE_MARKER_FILE}"
nymphs_sprite_touch_log
{
  printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'installed_module_version=%s\n' "${module_version}"
  printf 'install_root=%s\n' "${NYMPHS_SPRITE_INSTALL_DIR}"
  printf 'zimage_url=%s\n' "${NYMPHS_SPRITE_ZIMAGE_URL}"
  printf 'lora_root=%s\n' "${NYMPHS_SPRITE_LORA_ROOT}"
  printf 'lora_dir=%s\n' "${NYMPHS_SPRITE_LORA_DIR}"
  printf 'controlnet_dir=%s\n' "${NYMPHS_SPRITE_CONTROLNET_DIR}"
  printf 'depth_models_dir=%s\n' "${NYMPHS_SPRITE_DEPTH_MODELS_DIR}"
} >> "${NYMPHS_SPRITE_LOG_FILE}"

echo "installed_module_version=${module_version}"
echo "${NYMPHS_SPRITE_MODULE_NAME} installed."
