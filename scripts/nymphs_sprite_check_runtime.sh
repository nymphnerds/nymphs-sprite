#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

python_bin="$(nymphs_sprite_python_bin)"

"${python_bin}" - <<'PY'
from __future__ import annotations

import importlib
import inspect

print("runtime_check=nymphs-sprite")

try:
    import diffusers
    print(f"diffusers_version={diffusers.__version__}")
except Exception as exc:
    print(f"diffusers_error={type(exc).__name__}:{exc}")

try:
    from nunchaku import NunchakuZImageTransformer2DModel

    has_lora = all(
        hasattr(NunchakuZImageTransformer2DModel, name)
        for name in ("update_lora_params", "set_lora_strength", "reset_lora")
    )
    print(f"nunchaku_zimage_transformer=true")
    print(f"nunchaku_zimage_lora={str(has_lora).lower()}")
    print(f"nunchaku_zimage_forward_signature={inspect.signature(NunchakuZImageTransformer2DModel.forward)}")
except Exception as exc:
    print(f"nunchaku_zimage_transformer=false")
    print(f"nunchaku_zimage_error={type(exc).__name__}:{exc}")

for module_name in (
    "diffusers.pipelines.z_image.pipeline_z_image",
    "diffusers.pipelines.z_image.pipeline_z_image_img2img",
    "diffusers.pipelines.z_image.pipeline_z_image_controlnet",
    "diffusers.models.controlnets.controlnet_z_image",
):
    try:
        module = importlib.import_module(module_name)
        names = ",".join(name for name in dir(module) if "ZImage" in name or "Control" in name)
        print(f"module:{module_name}=true names={names}")
    except Exception as exc:
        print(f"module:{module_name}=false error={type(exc).__name__}:{exc}")

try:
    import transformers
    print(f"transformers_version={transformers.__version__}")
except Exception as exc:
    print(f"transformers_error={type(exc).__name__}:{exc}")

try:
    import controlnet_aux
    print("controlnet_aux=true")
except Exception as exc:
    print(f"controlnet_aux=false error={type(exc).__name__}:{exc}")
PY
