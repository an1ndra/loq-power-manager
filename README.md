# LOQ Power Manager

A small PyQt6 desktop application for controlling power profiles, battery
conservation mode, and monitoring sensors on Lenovo LOQ / IdeaPad laptops
running Linux.

It provides a Linux-native alternative to the Windows Lenovo Vantage / LOQ
app by using standard kernel sysfs interfaces such as `platform_profile`,
`conservation_mode`, and `hwmon`.

## Table of contents

1. [Project description](#project-description)
2. [User guide](#user-guide)
   - [Installation](#installation)
   - [Running](#running)
   - [Usage](#usage)
   - [Restore settings at login](#restore-settings-at-login)
3. [Developer guide](#developer-guide)
   - [Project structure](#project-structure)
   - [Running from source](#running-from-source)
   - [Building packages locally](#building-packages-locally)
   - [Contributing](#contributing)
4. [Safety notes](#safety-notes)
5. [Troubleshooting](#troubleshooting)

## 1. Project description

LOQ Power Manager lets Linux users on compatible Lenovo hardware:

- Switch ACPI power profiles (Silent, Balanced, Gaming, Custom).
- Toggle battery conservation mode, which limits charge to ~55–60%.
- Monitor CPU/GPU temperatures and any fan speeds exposed by the kernel.
- Save preferences and restore them automatically at login.

The application is intentionally limited to safe, documented sysfs interfaces.
It does not flash firmware, use undocumented ACPI calls, or modify system files
outside the known safe paths.

## 2. User guide

### Installation

#### Fedora / openSUSE / RHEL

Download the latest `.rpm` from the
[releases page](https://github.com/an1ndra/loq-power-manager/releases) and
install it:

```bash
sudo dnf install ./loq-power-manager-*.noarch.rpm
```

#### Debian / Ubuntu

Download the latest `.deb` from the
[releases page](https://github.com/an1ndra/loq-power-manager/releases) and
install it:

```bash
sudo apt install ./loq-power-manager_*_all.deb
```

#### Manual install from source

```bash
cd loq-power-manager
sudo ./install.sh
```

The installer places files under `/usr/local`, adds a desktop entry, and
installs a PolicyKit action.

### Running

After installation, launch the app from the application menu or run:

```bash
loq-power-manager
```

A system tray icon is shown while the app is running.

### Usage

- **Power tab**: select a power profile. The app maps friendly names to the
  actual values your firmware supports (for example, "Silent" may map to
  `low-power` or `quiet`).
- **Battery tab**: toggle conservation mode. If your laptop does not expose a
  configurable charge threshold, the threshold control is hidden automatically.
- **Sensors tab**: view CPU/GPU temperatures and available fan speeds.
- **About tab**: see which sysfs interfaces were detected on your system.

### Restore settings at login

Enable **"Restore these settings at next login"** in the Battery tab. The app
saves the current profile and conservation state and re-applies them at login.

You can also trigger a restore manually:

```bash
loq-power-manager --restore
```

## 3. Developer guide

### Project structure

```
loq-power-manager/
├── loq_power_manager/        # PyQt6 application
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

On Fedora or RHEL:

```bash
cd loq-power-manager
sudo dnf install -y rpm-build python3-devel python3-setuptools python3-wheel
./build-rpm.sh
```

The RPM is placed in `~/rpmbuild/RPMS/noarch/`.

#### DEB

On Debian or Ubuntu:

```bash
cd loq-power-manager
sudo apt install -y build-essential debhelper dh-python python3-all python3-setuptools
./build-deb.sh
```

The `.deb` is created in `/tmp`.

### Contributing

Contributions are welcome. To propose a change:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/my-change`).
3. Make your changes and keep them focused.
4. Run syntax checks:
   ```bash
   bash -n helpers/*.sh build-rpm.sh build-deb.sh install.sh
   python3 -m py_compile loq_power_manager/*.py setup.py
   ```
5. Commit with a clear message. Signed commits are appreciated.
6. Open a pull request against the `main` branch.

Please keep changes minimal and follow the existing coding style.

## 4. Safety notes

- Only standard Linux sysfs interfaces are used.
- Privileged writes are delegated to small helper scripts that run through
  `pkexec` / PolicyKit.
- Helper scripts whitelist the exact sysfs paths they can touch and validate
  every value before writing.
- Unsupported hardware controls are disabled automatically.
- This tool is provided as-is. Inspect the helper scripts in `helpers/` if you
  are unsure about any operation.

## 5. Troubleshooting

### No fan speed shown

Fan speed monitoring depends on the kernel exposing fan sensors through
`/sys/class/hwmon`. Many LOQ laptops do not expose both fans (or any fan) this
way. For fan control and monitoring on supported Legion/LOQ models, see the
community project [LenovoLegionLinux](https://github.com/johnfanv2/LenovoLegionLinux).

### Battery charge threshold is unavailable

Some Lenovo firmware only provides a binary conservation mode and not a
user-configurable charge threshold. In that case, the threshold control is
hidden and conservation mode is the only battery protection available from
Linux.

### pkexec password prompt every time

The PolicyKit action asks for the administrator password by default. To allow
passwordless operation, edit:

```
/usr/share/polkit-1/actions/com.anindra.loqpowermanager.policy
```

and change `auth_admin_keep` to `yes` for the desired actions. Only do this on
single-user machines.

### Power profile fails to apply

If a profile such as "Custom" is rejected by the kernel, the app will disable
that button. This usually means the firmware lists the profile as supported but
requires additional setup that is not exposed through sysfs.

## License

MIT
