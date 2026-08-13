#!/bin/bash
# Safe helper: set battery charge control end threshold.
# Usage: set_battery_threshold.sh <sysfs_path> <threshold>
set -euo pipefail

TARGET="${1:-}"
VALUE="${2:-}"

if [[ -z "$TARGET" || -z "$VALUE" ]]; then
    echo "Usage: $0 <sysfs_path> <threshold>" >&2
    exit 1
fi

# Only allow paths that look like battery charge thresholds.
if [[ ! "$TARGET" =~ charge_control_end_threshold$ ]]; then
    echo "Refusing to write to unrecognized path: $TARGET" >&2
    exit 1
fi

if [[ ! -e "$TARGET" ]]; then
    echo "Target does not exist: $TARGET" >&2
    exit 1
fi

if [[ ! "$VALUE" =~ ^[0-9]+$ ]]; then
    echo "Threshold must be an integer" >&2
    exit 1
fi

if (( VALUE < 20 || VALUE > 100 )); then
    echo "Threshold must be between 20 and 100" >&2
    exit 1
fi

printf '%d' "$VALUE" > "$TARGET"
echo "Set battery charge threshold to ${VALUE}%"
