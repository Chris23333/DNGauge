#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

CONDA_ENV="dng_compare"

if [[ -n "${PYTHON_BIN:-}" ]]; then
    PYTHON_CMD="${PYTHON_BIN}"
else
    # 自动获取当前机器的 conda 安装路径并激活 dng_compare 环境
    if command -v conda >/dev/null 2>&1; then
        CONDA_BASE="$(conda info --base)"
        # shellcheck disable=SC1091
        source "${CONDA_BASE}/etc/profile.d/conda.sh"
        conda activate "${CONDA_ENV}"
        PYTHON_CMD="$(command -v python)"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="$(command -v python3)"
    else
        PYTHON_CMD="$(command -v python)"
    fi
fi

cd "${PROJECT_ROOT}"

rm -rf "${PROJECT_ROOT}/build" "${PROJECT_ROOT}/dist"

"${PYTHON_CMD}" -m PyInstaller \
    --noconfirm \
    --distpath "${PROJECT_ROOT}/dist" \
    --workpath "${PROJECT_ROOT}/build" \
    "${SCRIPT_DIR}/DNGauge.spec"

echo
echo "Linux executable created:"
echo "  ${PROJECT_ROOT}/dist/DNGauge"
