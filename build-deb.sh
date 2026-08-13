#!/bin/bash
# Build a DEB package for LOQ Power Manager.
# Run this on Debian/Ubuntu (or any system with dpkg-buildpackage).
set -euo pipefail

NAME="loq-power-manager"
VERSION="0.2.0"

cd "$(dirname "$0")"

# Clean previous builds
rm -rf "../${NAME}_${VERSION}"

# Create a clean source tree
BUILD_DIR="/tmp/${NAME}-${VERSION}"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cp -r loq_power_manager helpers polkit debian "$BUILD_DIR/"
cp README.md LICENSE requirements.txt setup.py MANIFEST.in \
    loq-power-manager.desktop loq-power-manager-restore.desktop "$BUILD_DIR/"

# Remove __pycache__ and .pyc files
find "$BUILD_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -type f -name '*.pyc' -delete 2>/dev/null || true

# Build package
cd "$BUILD_DIR"
dpkg-buildpackage -us -uc -b

echo ""
echo "DEB built successfully:"
ls -la "/tmp/${NAME}_${VERSION}"*.deb 2>/dev/null || ls -la /tmp/*.deb
