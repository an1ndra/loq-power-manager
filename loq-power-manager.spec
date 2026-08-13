Name:           loq-power-manager
Version:        0.2.0
Release:        1%{?dist}
Summary:        Power profile and battery manager for Lenovo LOQ laptops

License:        MIT
URL:            https://github.com/an1ndra/loq-power-manager
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3
Requires:       python3
Requires:       python3-pyqt6
Requires:       polkit
Requires:       /usr/bin/pkexec

%description
LOQ Power Manager is a small PyQt6 application for controlling power profiles,
battery conservation mode, and monitoring CPU/GPU temperatures and fan speeds
on Lenovo LOQ / IdeaPad laptops.

%prep
%autosetup

# Patch polkit policy to use system helper paths
sed -i 's|/usr/local/lib/loq-power-manager/helpers|/usr/lib/loq-power-manager/helpers|g' \
    polkit/com.anindra.loqpowermanager.policy

%build
# Nothing to compile; this is a noarch Python application.

%install
# Application directory
install -dm755 %{buildroot}/usr/lib/%{name}/loq_power_manager
install -dm755 %{buildroot}/usr/lib/%{name}/helpers

# Python package
cp -r loq_power_manager/*.py %{buildroot}/usr/lib/%{name}/loq_power_manager/

# Helpers
install -Dm755 helpers/set_power_profile.sh %{buildroot}/usr/lib/%{name}/helpers/set_power_profile.sh
install -Dm755 helpers/set_battery_threshold.sh %{buildroot}/usr/lib/%{name}/helpers/set_battery_threshold.sh
install -Dm755 helpers/set_conservation_mode.sh %{buildroot}/usr/lib/%{name}/helpers/set_conservation_mode.sh

# Launcher
install -dm755 %{buildroot}/usr/bin
install -Dm755 /dev/stdin %{buildroot}/usr/bin/%{name} <<'EOF'
#!/bin/bash
exec python3 /usr/lib/loq-power-manager/loq_power_manager/main.py "$@"
EOF

# Polkit policy
install -Dm644 polkit/com.anindra.loqpowermanager.policy \
    %{buildroot}/usr/share/polkit-1/actions/com.anindra.loqpowermanager.policy

# Desktop files
install -Dm644 %{name}.desktop %{buildroot}/usr/share/applications/%{name}.desktop
install -Dm644 %{name}-restore.desktop %{buildroot}/usr/share/applications/%{name}-restore.desktop

# Autostart restore entry
install -Dm644 %{name}-restore.desktop %{buildroot}/etc/xdg/autostart/%{name}-restore.desktop

%files
%license LICENSE
%doc README.md
%{_bindir}/%{name}
/usr/lib/%{name}/
%{_datadir}/polkit-1/actions/com.anindra.loqpowermanager.policy
%{_datadir}/applications/%{name}.desktop
%{_datadir}/applications/%{name}-restore.desktop
/etc/xdg/autostart/%{name}-restore.desktop

%changelog
* Thu Aug 13 2026 Anindra <anindrakarmakar+git@proton.me> - 0.2.0-1
- Initial RPM package
