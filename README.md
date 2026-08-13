# LOQ Power Manager

A small PyQt6 desktop application for controlling power profiles, battery
conservation mode, and monitoring sensors on Lenovo LOQ / IdeaPad laptops
running Linux.

It is similar in spirit to the Windows Lenovo Vantage / LOQ app, but built on
top of standard Linux sysfs interfaces.

## Features

- **Power profiles**: switch between Silent, Balanced, Gaming, and Custom modes
  via the ACPI `platform_profile` interface.
- **Battery conservation mode**: toggle Lenovo `conservation_mode` to limit
  charge to ~55–60%.
- **Sensor monitoring**: read CPU/GPU temperatures and available fan speeds
  from `/sys/class/hwmon`.
- **Persistent settings**: optionally restore the last used profile and battery
  mode at login.
- **Packaging**: ready-to-use RPM and DEB build scripts plus a GitHub Actions
  workflow that publishes releases automatically.

## Safety design

- Only standard Linux sysfs interfaces are touched.
- All privileged writes use `pkexec` / PolicyKit.
- Helper scripts whitelist the exact sysfs paths they are allowed to write and
  validate every value before writing.
- Unsupported hardware controls are disabled automatically instead of crashing.

## User guide

### Installation

#### Fedora / openSUSE / RHEL (RPM)

Download the latest `.rpm` from the [releases page](https://github.com/an1ndra/loq-power-manager/releases)
and install it with `dnf`:

```bash
sudo dnf install ./loq-power-manager-*.noarch.rpm
```

#### Debian / Ubuntu (DEB)

Download the latest `.deb` from the [releases page](https://github.com/an1ndra/loq-power-manager/releases)
and install it with `apt`:

```bash
sudo apt install ./loq-power-manager_*_all.deb
```

#### Manual install from source

```bash
cd loq-power-manager
sudo ./install.sh
```

The installer will install the application under `/usr/local`, add a desktop
entry, and register a PolicyKit action.

### Running

After installation, launch the app from the application menu or run:

```bash
loq-power-manager
```

A system tray icon is also provided.

### What to expect

- The **Power** tab lets you select a power profile. The app automatically maps
  friendly names (Silent, Gaming, etc.) to whatever values your firmware
  supports.
- The **Battery** tab shows conservation mode. If your laptop does not expose a
  configurable charge threshold, the threshold control is hidden automatically.
- The **Sensors** tab shows live CPU/GPU temperatures and any fan speeds the
  kernel exposes.
- The **About** tab lists the sysfs interfaces detected on your system.

### Restore settings at login

Enable **"Restore these settings at next login"** in the Battery tab. The app
will re-apply the saved profile and conservation mode on the next login.

You can also trigger a restore manually:

```bash
loq-power-manager --restore
```

## Developer guide

### Project structure

```
loq-power-manager/
├── loq_power_manager/        # PyQt6 application code
│   ├── backend.py            # sysfs detection and control
│   ├── main.py               # GUI and system tray
│   ├── sensors.py            # hwmon sensor reading
│   └── __main__.py           # package entry point
├── helpers/                  # pkexec helper shell scripts
├── polkit/                   # PolicyKit action definition
├── debian/                   # DEB packaging files
├── loq-power-manager.spec    # RPM spec file
├── build-deb.sh            # DEB build script
├── build-rpm.sh            # RPM build script
├── install.sh              # Manual install script
└── .github/workflows/        # CI/CD workflows
```

### Running from source

```bash
cd loq-power-manager
pip3 install --user PyQt6      # or: sudo dnf install python3-pyqt6
python3 -m loq_power_manager
```

### Building packages locally

#### RPM

On a Fedora/RHEL system:

```bash
cd loq-power-manager
sudo dnf install -y rpm-build python3-devel python3-setuptools python3-wheel
./build-rpm.sh
```

The RPM is placed in `~/rpmbuild/RPMS/noarch/`.

#### DEB

On a Debian/Ubuntu system:

```bash
cd loq-power-manager
sudo apt install -y build-essential debhelper dh-python python3-all python3-setuptools
./build-deb.sh
```

The `.deb` is created in `/tmp`.

## Release process

This repository uses a GitHub Actions workflow (`.github/workflows/release.yml`)
to build packages and publish releases automatically.

### Creating a normal release

1. Make sure the version has been bumped in:
   - `setup.py`
   - `loq-power-manager.spec`
   - `debian/changelog`
   - `build-deb.sh` and `build-rpm.sh`

2. Commit the version bump.

3. Push a tag starting with `v`:

   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0
   ```

4. The workflow will build the RPM and DEB packages and create a GitHub
   release at:
   https://github.com/an1ndra/loq-power-manager/releases

### Creating a pre-release

Push a tag that contains `-pre`, `-alpha`, `-beta`, or `-rc`:

```bash
git tag -a v0.1.0-pre1 -m "Pre-release v0.1.0-pre1"
git push origin v0.1.0-pre1
```

The workflow will automatically mark the GitHub release as a **pre-release**.

### Manual release trigger

You can also trigger the workflow manually from the GitHub Actions tab:
https://github.com/an1ndra/loq-power-manager/actions

## Uninstall

### RPM

```bash
sudo dnf remove loq-power-manager
```

### DEB

```bash
sudo apt remove loq-power-manager
```

### Manual install

If you used `./install.sh`:

```bash
sudo rm -rf /usr/local/lib/loq-power-manager
sudo rm -f /usr/local/bin/loq-power-manager
sudo rm -f /usr/local/share/applications/loq-power-manager*.desktop
sudo rm -f /usr/local/share/polkit-1/actions/com.anindra.loqpowermanager.policy
rm -f ~/.config/autostart/loq-power-manager-restore.desktop
```

## Troubleshooting

### No fan speed shown

Not all Lenovo laptops expose fan speed sensors through `/sys/class/hwmon`. If
no fan inputs are present, the Sensors tab will show "Not available". For fan
control and monitoring on supported Legion/LOQ models, see the community
project [LenovoLegionLinux](https://github.com/johnfanv2/LenovoLegionLinux).

### Battery charge threshold is unavailable

Some LOQ/IdeaPad firmware only exposes a binary conservation mode and not a
configurable charge threshold. In that case, the threshold control is hidden and
conservation mode is the only battery protection available from Linux.

### pkexec password prompt appears every time

The PolicyKit action is configured to ask for the administrator password. To
allow passwordless operation for the active user, edit:

```
/usr/share/polkit-1/actions/com.anindra.loqpowermanager.policy
```

and change `auth_admin_keep` to `yes` for the desired actions. Only do this on
single-user machines.

## License

MIT
