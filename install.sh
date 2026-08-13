#!/bin/bash
# Install LOQ Power Manager on Fedora KDE (or other Linux distributions).
set -euo pipefail

INSTALL_PREFIX="${INSTALL_PREFIX:-/usr/local}"
APP_NAME="loq-power-manager"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

need_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "ERROR: '$1' is required but not installed." >&2
        exit 1
    fi
}

echo "==> LOQ Power Manager installer"
echo "    Source: $SRC_DIR"
echo "    Prefix: $INSTALL_PREFIX"

need_cmd python3
need_cmd pkexec

# Install distribution dependencies on Fedora
if command -v dnf >/dev/null 2>&1; then
    echo "==> Installing dependencies with dnf..."
    # Fedora uses python3-pyqt6 (or python3-qt6 on some spins); try the common names.
    sudo dnf install -y python3-pyqt6 polkit || true
    if ! python3 -c "import PyQt6" 2>/dev/null; then
        sudo dnf install -y python3-qt6 polkit || true
    fi
fi

# Ensure PyQt6 is available; fall back to pip if the distro package is missing.
if ! python3 -c "import PyQt6" 2>/dev/null; then
    echo "==> PyQt6 not found, trying pip install..."
    if ! python3 -m pip --version >/dev/null 2>&1; then
        echo "==> pip not found, installing python3-pip..."
        if command -v dnf >/dev/null 2>&1; then
            sudo dnf install -y python3-pip
        else
            echo "ERROR: python3-pip could not be installed automatically." >&2
            exit 1
        fi
    fi
    python3 -m pip install --user PyQt6 || {
        echo "ERROR: Failed to install PyQt6. Try: sudo dnf install python3-pyqt6" >&2
        exit 1
    }
fi

# Create directories
echo "==> Creating directories..."
sudo mkdir -p "$INSTALL_PREFIX/lib/$APP_NAME/helpers"
sudo mkdir -p "$INSTALL_PREFIX/bin"
sudo mkdir -p "$INSTALL_PREFIX/share/applications"
sudo mkdir -p "$INSTALL_PREFIX/share/polkit-1/actions"

# Copy Python package
echo "==> Copying application files..."
sudo cp -r "$SRC_DIR/loq_power_manager" "$INSTALL_PREFIX/lib/$APP_NAME/"

# Copy helpers and make them executable
sudo cp "$SRC_DIR/helpers/"*.sh "$INSTALL_PREFIX/lib/$APP_NAME/helpers/"
sudo chmod 755 "$INSTALL_PREFIX/lib/$APP_NAME/helpers/"*.sh

# Create wrapper script
echo "==> Creating launcher..."
sudo tee "$INSTALL_PREFIX/bin/$APP_NAME" >/dev/null <<EOF
#!/bin/bash
exec python3 $INSTALL_PREFIX/lib/$APP_NAME/loq_power_manager/main.py "\$@"
EOF
sudo chmod 755 "$INSTALL_PREFIX/bin/$APP_NAME"

# Install desktop files
echo "==> Installing desktop entries..."
sudo cp "$SRC_DIR/$APP_NAME.desktop" "$INSTALL_PREFIX/share/applications/"
sudo cp "$SRC_DIR/$APP_NAME-restore.desktop" "$INSTALL_PREFIX/share/applications/"

# Install polkit policy with correct helper paths
POLICY_FILE="/tmp/com.anindra.loqpowermanager.policy"
sed "s|/usr/local/lib/loq-power-manager/helpers|$INSTALL_PREFIX/lib/$APP_NAME/helpers|g" \
    "$SRC_DIR/polkit/com.anindra.loqpowermanager.policy" > "$POLICY_FILE"
echo "==> Installing polkit policy..."
sudo cp "$POLICY_FILE" "$INSTALL_PREFIX/share/polkit-1/actions/"
rm -f "$POLICY_FILE"

# Optional: install autostart restore entry
AUTOSTART_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
mkdir -p "$AUTOSTART_DIR"
cp "$INSTALL_PREFIX/share/applications/$APP_NAME-restore.desktop" "$AUTOSTART_DIR/"

echo ""
echo "==> Installation complete!"
echo "    Run: $APP_NAME"
echo "    Or find 'LOQ Power Manager' in your application menu."
echo ""
echo "NOTE: The polkit policy is configured to ask for the admin password."
echo "      You can edit $INSTALL_PREFIX/share/polkit-1/actions/com.anindra.loqpowermanager.policy"
echo "      if you want passwordless operation for the wheel group."
