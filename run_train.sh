#!/usr/bin/env bash
# run_train.sh — launch an RL training run inside the project's .venv.
#
# Why this wrapper exists:
#   run_train.py relies on SubprocVecEnv (multiprocessing). When PYTHONPATH carries
#   foreign paths (e.g. ROS / IsaacLab / IsaacGym), the forked env workers import
#   mismatched copies of gymnasium/tqdm from outside the venv, crash, and the parent
#   process only sees a bare EOFError. We unset PYTHONPATH so every import resolves
#   to the project venv and nothing else.
#
# Usage (from anywhere; the project root is located automatically):
#   ./run_train.sh
#   ./run_train.sh --config_file_path rl_train/train/train_configs/xxx.json
#   ./run_train.sh --config_file_path xxx.json --flag_rendering \
#                  --config.env_params.terrain_type flat
#
# Optional env var: MYOASSIST_NUM_THREADS (defaults to 8 inside run_train.py).

set -euo pipefail

# Project root = directory containing this script (callable from any CWD)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "ERROR: venv python not found at $PYTHON_BIN" >&2
    echo "Create it with:  cd $ROOT_DIR && uv venv && uv pip install -e ." >&2
    exit 1
fi

# Drop inherited ROS/IsaacLab/... paths: the venv is the only source of truth.
unset PYTHONPATH

DEFAULT_CONFIG="rl_train/train/train_configs/imitation_tutorial_22_separated_net_partial_obs.json"
DEFAULT_CONFIG="rl_train/train/train_configs/device_sweep/imitation_22_DephyExoBoot_L1_h128_e32_sidenet_mirror0p1_actpen10.json"


ARGS=("$@")
if [[ "$*" != *"--config_file_path"* ]]; then
    ARGS+=(--config_file_path "$DEFAULT_CONFIG")
fi

echo ">>> project root:  $ROOT_DIR"
echo ">>> python:        $PYTHON_BIN"
echo ">>> command:       python rl_train/run_train.py ${ARGS[*]}"

exec "$PYTHON_BIN" rl_train/run_train.py "${ARGS[@]}"
