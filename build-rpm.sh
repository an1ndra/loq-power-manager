#!/bin/bash
# Build an RPM package for LOQ Power Manager.
# Run this on Fedora (or any system with rpm-build and rpmbuild).
set -euo pipefail

NAME="loq-power-manager"
VERSION="0.2.0"
RELEASE="1"

# Prepare workspace
mkdir -p ~/rpmbuild/{SOURCES,SPECS,BUILD,RPMS,SRPMS}

# Remember project directory
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARBALL="${NAME}-${VERSION}.tar.gz"
SOURCE_DIR="/tmp/${NAME}-${VERSION}"
rm -rf "$SOURCE_DIR"
mkdir -p "$SOURCE_DIR"

# Copy source files
cd "$PROJECT_DIR"
cp -r loq_power_manager helpers polkit "$SOURCE_DIR/"
cp -r README.md LICENSE requirements.txt setup.py MANIFEST.in loq-power-manager.desktop \
    loq-power-manager-restore.desktop loq-power-manager.spec "$SOURCE_DIR/"

# Remove __pycache__ and .pyc files
find "$SOURCE_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$SOURCE_DIR" -type f -name '*.pyc' -delete 2>/dev/null || true

# Create tarball
cd /tmp
tar czf "${HOME}/rpmbuild/SOURCES/${TARBALL}" "${NAME}-${VERSION}"
rm -rf "$SOURCE_DIR"

cd "$PROJECT_DIR"
cp "${NAME}.spec" ~/rpmbuild/SPECS/

# Build RPM
# Use --nodeps when building on non-RPM hosts (e.g. Ubuntu container) because
# the build dependencies are satisfied by the host Python toolchain.
if rpm -q python3-devel >/dev/null 2>&1; then
    rpmbuild -ba ~/rpmbuild/SPECS/${NAME}.spec
else
    echo "Note: building RPM without RPM-level dependency checks (non-RPM host)."
    rpmbuild -ba --nodeps ~/rpmbuild/SPECS/${NAME}.spec
fi

echo ""
echo "RPM built successfully:"
find ~/rpmbuild/RPMS -name "${NAME}-*.rpm"
find ~/rpmbuild/SRPMS -name "${NAME}-*.src.rpm"
