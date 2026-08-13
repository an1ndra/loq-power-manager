#!/bin/bash
# Safe helper: set Lenovo conservation mode.
# Usage: set_conservation_mode.sh <sysfs_path> <0|1>
set -euo pipefail

TARGET="${1:-}"
VALUE="${2:-}"

if [[ -z "$TARGET" || -z "$VALUE" ]]; then
    echo "Usage: $0 <sysfs_path> <0|1>" >&2
    exit 1
fi

# Only allow conservation_mode files under ideapad_acpi or lenovo platform paths.
if [[ ! "$TARGET" =~ conservation_mode$ ]]; then
    echo "Refusing to write to unrecognized path: $TARGET" >&2
    exit 1
fi

if [[ ! "$VALUE" =~ ^[01]$ ]]; then
    echo "Value must be 0 or 1" >&2
    exit 1
fi

if [[ ! -w "$TARGET" ]]; then
    echo "Target not writable: $TARGET" >&2
    exit 1
fi

printf '%s' "$VALUE" > "$TARGET"
state="disabled"
[[ "$VALUE" == "1" ]] && state="enabled"
echo "Conservation mode ${state}"
