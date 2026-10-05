#!/usr/bin/env bash
# Odtwarza środowisko pipeline'u w nowej sesji (kontener jest ulotny).
# Użycie: bash pipeline/setup_env.sh [WORKDIR]   (domyślnie: $SCRATCH lub ./work)
# Wymaga sieci: pypi, github.com, huggingface.co (+ *.hf.co).
set -euo pipefail
W="${1:-${SCRATCH:-$PWD/work}}"
mkdir -p "$W" && cd "$W"
echo "workdir: $W"; df -h . | tail -1

# 1) Blender (bpy) w OSOBNYM venv: globalny numpy 2.x psuje bpy 5.0.1
if [ ! -x bvenv/bin/python ]; then
  python3 -m venv bvenv
  bvenv/bin/pip install -q bpy==5.0.1 trimesh networkx lxml scipy rtree embreex pillow matplotlib manifold3d fast-simplification
fi
bvenv/bin/python -c "import bpy, trimesh; print('bpy', bpy.app.version_string)"

# 2) Hunyuan3D-2 na CPU (bryły bez limitu GPU)
if [ ! -x hyvenv/bin/python ]; then
  python3 -m venv --system-site-packages hyvenv   # torch z systemu
  hyvenv/bin/pip install -q diffusers transformers einops omegaconf accelerate opencv-python-headless pymeshlab trimesh scikit-image rembg onnxruntime huggingface_hub
fi
[ -d Hunyuan3D-2 ] || git clone --depth 1 https://github.com/Tencent-Hunyuan/Hunyuan3D-2
export HY3DGEN_MODELS="$W/models"
hyvenv/bin/python - <<'EOF'
import os
from huggingface_hub import snapshot_download
root = os.environ['HY3DGEN_MODELS']
for repo, sub in [('tencent/Hunyuan3D-2mini', 'hunyuan3d-dit-v2-mini-turbo'),
                  ('tencent/Hunyuan3D-2mv', 'hunyuan3d-dit-v2-mv-turbo')]:
    snapshot_download(repo, local_dir=os.path.join(root, repo),
                      allow_patterns=[f'{sub}/*', 'hunyuan3d-vae-v2-*turbo/*'])
print('weights in', root)
EOF

# 3) Klient Space'ów HF (edycje 2D: FLUX Kontext)
python3 -m pip install -q gradio_client
python3 -c "import os; print('HF_TOKEN set' if os.environ.get('HF_TOKEN') else 'BRAK HF_TOKEN (dodaj w ustawieniach środowiska, potem NOWA sesja)')"

# 4) Slicer do G-code (FDM / Banach): PrusaSlicer z apt (GitHub releases bywa blokowany)
command -v prusa-slicer >/dev/null || (apt-get install -y -q prusa-slicer >/dev/null 2>&1 || echo "prusa-slicer: instalacja nieudana")
echo "OK. W skryptach ustaw ścieżki: Hunyuan3D-2 i models są w $W"
