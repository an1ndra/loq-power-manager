#!/bin/bash
# Safe helper: set ACPI platform_profile.
# Usage: set_power_profile.sh <sysfs_path> <profile_value>
set -euo pipefail

TARGET="${1:-}"
VALUE="${2:-}"

ALLOWED_PATHS=(
    "/sys/firmware/acpi/platform_profile"
)

is_allowed() {
    local target="$1"
    for p in "${ALLOWED_PATHS[@]}"; do
        if [[ "$target" == "$p" ]]; then
            return 0
        fi
    done
    return 1
}

if [[ -z "$TARGET" || -z "$VALUE" ]]; then
    echo "Usage: $0 <sysfs_path> <profile_value>" >&2
    exit 1
fi

if ! is_allowed "$TARGET"; then
    echo "Refusing to write to unrecognized path: $TARGET" >&2
    exit 1
fi

if [[ ! -w "$TARGET" ]]; then
    echo "Target not writable: $TARGET" >&2
    exit 1
fi

# Validate value against allowed choices if available.
CHOICES_FILE="/sys/firmware/acpi/platform_profile_choices"
if [[ -r "$CHOICES_FILE" ]]; then
    if ! grep -qw "$VALUE" "$CHOICES_FILE"; then
        echo "Profile '$VALUE' not in allowed choices" >&2
        exit 1
    fi
fi

if ! printf '%s' "$VALUE" > "$TARGET" 2>/dev/null; then
    echo "Kernel rejected profile '$VALUE'. " \
         "This profile may be listed as supported but require additional firmware setup." >&2
    exit 1
fi
echo "Set platform_profile to '$VALUE'"
