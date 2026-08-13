# LOQ Power Manager

A small PyQt6 application for Fedora KDE that lets you change the power mode
(Silent, Balanced, Gaming, Custom), enable battery conservation mode, and
monitor CPU/GPU temperature and fan speed on Lenovo LOQ / IdeaPad laptops —
similar to the Windows Lenovo Vantage / LOQ app.

## What it does

- Reads and writes `/sys/firmware/acpi/platform_profile` to switch power modes.
- Reads and writes the Lenovo `conservation_mode` sysfs file (limits charge to
  ~55–60%).
- Reads CPU/GPU temperatures and fan speeds from `/sys/class/hwmon`.
- Hides unsupported controls automatically (e.g. charge limit on models that
  only expose conservation mode).
- Saves your preferences and optionally restores them at login.

## Safety design

This tool is intentionally limited and defensive:

- **Only standard sysfs interfaces** are touched. No firmware flashing, no
  embedded controller poking, no undocumented WMI calls.
- **All values are validated** before any write:
  - power profiles are checked against `platform_profile_choices`;
  - battery threshold must be an integer between 20 and 100;
  - conservation mode only accepts `0` or `1`.
- **Privileged helpers** run through `pkexec` / PolicyKit, so you explicitly
  authorize every change.
- **Helper scripts whitelist** the exact sysfs paths they are allowed to write.
  They refuse to touch anything else.
- **Missing hardware is handled gracefully**: unsupported controls are disabled
  automatically instead of crashing.

That said, this is provided as-is. If you are uncomfortable, inspect the small
shell scripts in `helpers/` before installing.

## Requirements

- Fedora KDE (or any Linux distribution with KDE Plasma)
- Python 3
- PyQt6 (`python3-pyqt6` package on Fedora)
- `polkit` / `pkexec`
- A Lenovo LOQ / IdeaPad / Legion system that exposes the sysfs interfaces above.

## Quick install

```bash
cd loq-power-manager
./install.sh
```

The installer will:

1. Install `python3-pyqt6` and `polkit` if running on Fedora.
2. Copy the application to `/usr/local/lib/loq-power-manager`.
3. Install a launcher at `/usr/local/bin/loq-power-manager`.
4. Install a PolicyKit action.
5. Add a desktop entry to your application menu.
6. Add an autostart entry that restores your last saved settings at login.

Then run it:

```bash
loq-power-manager
```

## Manual run (without installing)

```bash
cd loq-power-manager
pip3 install --user PyQt6          # if not already installed
python3 -m loq_power_manager.main
```

## Check your hardware is supported

Before running, you can verify the needed files exist on your Fedora host:

```bash
# Power profiles
ls /sys/firmware/acpi/platform_profile
ls /sys/firmware/acpi/platform_profile_choices

# Battery charge threshold (one of these usually exists)
ls /sys/class/power_supply/BAT*/charge_control_end_threshold

# Lenovo conservation mode (often on IdeaPad/LOQ)
find /sys/bus/platform/drivers/ideapad_acpi -name conservation_mode
```

If some files are missing, the corresponding GUI control will be disabled but
the rest of the app still works.

## Restore at login

Enable **"Restore these settings at next login"** in the app. The installer
already places an autostart entry; the app simply re-applies the saved profile,
threshold, and conservation mode when you log in.

You can also trigger a restore manually:

```bash
loq-power-manager --restore
```

## Sensors and fan control

The app can read CPU/GPU temperatures and fan speeds from `/sys/class/hwmon`.
This is **read-only monitoring**.

Direct fan control is **not** implemented because Lenovo LOQ/IdeaPad laptops do
not expose a standard sysfs interface for it. If you need fan curves, look at
the community project **LenovoLegionLinux**.

## Building packages

### RPM (Fedora)

```bash
cd loq-power-manager
sudo dnf install -y rpm-build python3-devel python3-setuptools python3-wheel
./build-rpm.sh
```

The RPM will be in `~/rpmbuild/RPMS/noarch/`.

### DEB (Debian / Ubuntu)

```bash
cd loq-power-manager
sudo apt install -y build-essential debhelper dh-python python3-all python3-setuptools python3-pyqt6
./build-deb.sh
```

The `.deb` will be created in `/tmp`.

### Automated GitHub releases

A GitHub Actions workflow (`.github/workflows/release.yml`) automatically
builds both the RPM and DEB packages and publishes them to a GitHub release
whenever you push a tag starting with `v`:

```bash
git tag v0.0.1
git push origin v0.0.1
```

After the workflow finishes, the packages will be attached to the release at
`https://github.com/an1ndra/loq-power-manager/releases`.

## Uninstall

```bash
sudo rm -rf /usr/local/lib/loq-power-manager
sudo rm -f /usr/local/bin/loq-power-manager
sudo rm -f /usr/local/share/applications/loq-power-manager*.desktop
sudo rm -f /usr/local/share/polkit-1/actions/com.anindra.loqpowermanager.policy
rm -f ~/.config/autostart/loq-power-manager-restore.desktop
```

## Troubleshooting

### “pkexec not authorized”

If you cancel the password dialog, the change is not applied. Re-try and enter
your password. The polkit policy is set to `auth_admin_keep`, so after the
first successful auth the helper will not ask again for a few minutes.

### No interfaces detected

Some firmware/BIOS versions do not expose the sysfs files. On LOQ machines,
make sure you are not in a container/VM when checking, and verify the kernel
module `ideapad_laptop` is loaded:

```bash
lsmod | grep ideapad
```

### Polkit password prompt every time

Edit `/usr/local/share/polkit-1/actions/com.anindra.loqpowermanager.policy`
and change `auth_admin_keep` to `yes` for the actions you want to be
passwordless. Only do this if you are the only user of the machine.

## License

MIT
