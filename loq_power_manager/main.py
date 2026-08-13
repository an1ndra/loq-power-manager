"""
LOQ Power Manager - PyQt6 GUI for Lenovo LOQ / IdeaPad power settings.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add package root to path when running from source tree.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from PyQt6 import QtCore, QtGui, QtWidgets
except ImportError as exc:
    print("PyQt6 is not installed. Run: sudo dnf install python3-pyqt6")
    raise SystemExit(1) from exc

from loq_power_manager.backend import PowerBackend, DEFAULT_MODES, PowerMode
from loq_power_manager.sensors import SensorMonitor


# ---------------------------------------------------------------------------
# Styled widgets
# ---------------------------------------------------------------------------
class ModeCard(QtWidgets.QFrame):
    """A clickable card representing a power mode."""

    clicked = QtCore.pyqtSignal()

    def __init__(self, mode: PowerMode, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.mode = mode
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(90)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self._selected = False
        self._enabled = True

        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 12, 16, 12)

        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setPixmap(
            QtGui.QIcon.fromTheme(mode.icon).pixmap(40, 40)
        )
        self.icon_label.setFixedSize(44, 44)
        layout.addWidget(self.icon_label)

        text_layout = QtWidgets.QVBoxLayout()
        self.title_label = QtWidgets.QLabel(mode.label)
        self.title_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        text_layout.addWidget(self.title_label)

        self.desc_label = QtWidgets.QLabel(mode.description)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("font-size: 12px; color: palette(mid);")
        text_layout.addWidget(self.desc_label)
        layout.addLayout(text_layout, 1)

        self._apply_style()

    def _apply_style(self) -> None:
        if not self._enabled:
            self.setStyleSheet("""
                ModeCard {
                    background: palette(alternate-base);
                    border: 1px solid palette(mid);
                    border-radius: 10px;
                }
            """)
            self.title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: palette(mid);")
            self.desc_label.setStyleSheet("font-size: 12px; color: palette(mid);")
        elif self._selected:
            self.setStyleSheet("""
                ModeCard {
                    background: palette(highlight);
                    border: 2px solid palette(highlight);
                    border-radius: 10px;
                }
                QLabel { color: palette(highlighted-text); }
            """)
        else:
            self.setStyleSheet("""
                ModeCard {
                    background: palette(base);
                    border: 1px solid palette(mid);
                    border-radius: 10px;
                }
                ModeCard:hover {
                    background: palette(alternate-base);
                    border: 1px solid palette(highlight);
                }
            """)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._apply_style()

    def set_mode_enabled(self, enabled: bool, text: str | None = None) -> None:
        self._enabled = enabled
        if text:
            self.desc_label.setText(text)
        self._apply_style()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._enabled:
            self.clicked.emit()
        super().mousePressEvent(event)


class SensorCard(QtWidgets.QFrame):
    """A small card showing a sensor value."""

    def __init__(self, title: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            SensorCard {
                background: palette(base);
                border: 1px solid palette(mid);
                border-radius: 10px;
            }
        """)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setStyleSheet("font-size: 12px; color: palette(mid);")
        layout.addWidget(self.title_label)

        self.value_label = QtWidgets.QLabel("--")
        self.value_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, backend: PowerBackend) -> None:
        super().__init__()
        self.backend = backend
        self.sensor_monitor = SensorMonitor()
        self.setWindowTitle("LOQ Power Manager")
        self.setMinimumSize(560, 520)

        self._build_ui()
        self._load_state()
        self._refresh_status()

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QtWidgets.QLabel("LOQ Power Manager")
        header.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(header)

        subtitle = QtWidgets.QLabel(
            "Power profiles, battery conservation, and sensor monitoring for Lenovo LOQ."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: palette(mid);")
        layout.addWidget(subtitle)

        # Compatibility warning
        self.compat_label = QtWidgets.QLabel()
        self.compat_label.setWordWrap(True)
        self.compat_label.setStyleSheet(
            "padding: 10px; border-radius: 8px; background: #ffaa0022; color: #aa5500;"
        )
        self.compat_label.setVisible(False)
        layout.addWidget(self.compat_label)

        # Tabs
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self._build_power_tab(), "Power")
        self.tabs.addTab(self._build_battery_tab(), "Battery")
        self.tabs.addTab(self._build_sensors_tab(), "Sensors")
        self.tabs.addTab(self._build_about_tab(), "About")
        layout.addWidget(self.tabs)

        # Status bar
        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")

    def _build_power_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)

        info = QtWidgets.QLabel("Select a power profile. Silent maps to the lowest-power profile your firmware supports.")
        info.setWordWrap(True)
        info.setStyleSheet("color: palette(mid);")
        layout.addWidget(info)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(12)

        self.mode_cards: list[ModeCard] = []
        for index, mode in enumerate(DEFAULT_MODES):
            card = ModeCard(mode)
            card.clicked.connect(self._on_mode_clicked)
            self.mode_cards.append(card)
            grid.addWidget(card, index // 2, index % 2)

        layout.addLayout(grid)
        layout.addStretch()
        return tab

    def _build_battery_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setContentsMargins(8, 8, 8, 8)

        # Conservation mode card
        conservation_card = QtWidgets.QFrame()
        conservation_card.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        conservation_card.setStyleSheet("""
            QFrame {
                background: palette(base);
                border: 1px solid palette(mid);
                border-radius: 10px;
            }
        """)
        c_layout = QtWidgets.QHBoxLayout(conservation_card)
        c_layout.setSpacing(16)
        c_layout.setContentsMargins(16, 14, 16, 14)

        icon = QtWidgets.QLabel()
        icon.setPixmap(QtGui.QIcon.fromTheme("battery-good").pixmap(36, 36))
        c_layout.addWidget(icon)

        text_layout = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel("Conservation mode")
        title.setStyleSheet("font-size: 15px; font-weight: bold;")
        text_layout.addWidget(title)

        desc = QtWidgets.QLabel(
            "Limits charge to ~55–60% to extend battery lifespan. "
            "Turn off when you need a full charge."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: palette(mid);")
        text_layout.addWidget(desc)
        c_layout.addLayout(text_layout, 1)

        self.conservation_check = QtWidgets.QCheckBox()
        self.conservation_check.setMinimumSize(48, 24)
        self.conservation_check.stateChanged.connect(self._on_conservation_changed)
        c_layout.addWidget(self.conservation_check)

        layout.addWidget(conservation_card)

        # Charge threshold (only if supported)
        self.threshold_card = QtWidgets.QFrame()
        self.threshold_card.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.threshold_card.setStyleSheet("""
            QFrame {
                background: palette(base);
                border: 1px solid palette(mid);
                border-radius: 10px;
            }
        """)
        t_layout = QtWidgets.QVBoxLayout(self.threshold_card)
        t_layout.setSpacing(10)
        t_layout.setContentsMargins(16, 14, 16, 14)

        t_title = QtWidgets.QLabel("Custom charge limit")
        t_title.setStyleSheet("font-size: 15px; font-weight: bold;")
        t_layout.addWidget(t_title)

        slider_layout = QtWidgets.QHBoxLayout()
        self.threshold_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(20, 100)
        self.threshold_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.threshold_slider.setTickInterval(10)
        self.threshold_slider.valueChanged.connect(self._on_threshold_moved)
        slider_layout.addWidget(self.threshold_slider)

        self.threshold_value_label = QtWidgets.QLabel("80%")
        self.threshold_value_label.setMinimumWidth(40)
        self.threshold_value_label.setStyleSheet("font-weight: bold;")
        slider_layout.addWidget(self.threshold_value_label)

        self.btn_apply_threshold = QtWidgets.QPushButton("Apply")
        self.btn_apply_threshold.clicked.connect(self._apply_threshold)
        slider_layout.addWidget(self.btn_apply_threshold)
        t_layout.addLayout(slider_layout)

        layout.addWidget(self.threshold_card)

        # Unsupported threshold note
        self.threshold_unsupported_label = QtWidgets.QLabel(
            "Custom charge threshold is not supported on this model. "
            "Use conservation mode above."
        )
        self.threshold_unsupported_label.setWordWrap(True)
        self.threshold_unsupported_label.setStyleSheet("color: palette(mid); padding: 8px;")
        layout.addWidget(self.threshold_unsupported_label)

        # Auto-restore
        self.auto_restore_check = QtWidgets.QCheckBox("Restore these settings at next login")
        self.auto_restore_check.setToolTip("Saves current profile and conservation state so they are reapplied automatically.")
        layout.addWidget(self.auto_restore_check)

        layout.addStretch()
        return tab

    def _build_sensors_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)

        info = QtWidgets.QLabel(
            "Live sensor readings from /sys/class/hwmon. "
            "Fan control is not available natively on LOQ; see LenovoLegionLinux for fan curves."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: palette(mid);")
        layout.addWidget(info)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(12)

        self.cpu_card = SensorCard("CPU temperature")
        self.gpu_card = SensorCard("GPU temperature")
        self.fan_card = SensorCard("Fan speed")
        self.other_card = SensorCard("Other temperatures")
        self.other_card.value_label.setStyleSheet("font-size: 13px; font-weight: normal;")

        grid.addWidget(self.cpu_card, 0, 0)
        grid.addWidget(self.gpu_card, 0, 1)
        grid.addWidget(self.fan_card, 1, 0)
        grid.addWidget(self.other_card, 1, 1)

        layout.addLayout(grid)

        self.sensors_refresh_btn = QtWidgets.QPushButton("Refresh now")
        self.sensors_refresh_btn.clicked.connect(self._refresh_sensors)
        layout.addWidget(self.sensors_refresh_btn)

        layout.addStretch()
        return tab

    def _build_about_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)

        text = QtWidgets.QTextEdit()
        text.setReadOnly(True)

        supported = self.backend.supported()
        paths = []
        if self.backend.platform_profile_path:
            paths.append(f"Profile: {self.backend.platform_profile_path}")
        if self.backend.battery_threshold_path:
            paths.append(f"Threshold: {self.backend.battery_threshold_path}")
        if self.backend.conservation_mode_path:
            paths.append(f"Conservation: {self.backend.conservation_mode_path}")

        html = (
            "<h2>LOQ Power Manager</h2>"
            "<p>A simple Qt utility for controlling power settings on Lenovo LOQ / IdeaPad laptops.</p>"
            "<p><b>Safety notes:</b></p>"
            "<ul>"
            "<li>All privileged writes use pkexec and target only standard Linux sysfs interfaces.</li>"
            "<li>Values are validated before being written.</li>"
            "<li>If a feature is missing on your hardware, its control is automatically disabled.</li>"
            "<li>You can verify every command in the helper scripts under <code>helpers/</code>.</li>"
            "</ul>"
            "<p><b>Detected interfaces:</b></p>"
            "<ul>"
        )
        for p in paths or ["None detected"]:
            html += f"<li>{p}</li>"
        html += "</ul>"

        text.setHtml(html)
        layout.addWidget(text)
        layout.addStretch()
        return tab

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------
    def _load_state(self) -> None:
        state = self.backend.load_saved_state()
        if "profile" in state:
            self._select_mode(state["profile"])
        if "threshold" in state:
            try:
                self.threshold_slider.setValue(int(state["threshold"]))
            except ValueError:
                pass
        if "conservation" in state:
            self.conservation_check.setChecked(state["conservation"] == "1")
        if "auto_restore" in state:
            self.auto_restore_check.setChecked(state["auto_restore"] == "1")

    def _save_state(self) -> None:
        state: dict[str, str] = {}
        selected = self._selected_mode()
        if selected:
            effective = self.backend.effective_profile_for(selected)
            if effective:
                state["profile"] = effective
        state["threshold"] = str(self.threshold_slider.value())
        state["conservation"] = "1" if self.conservation_check.isChecked() else "0"
        state["auto_restore"] = "1" if self.auto_restore_check.isChecked() else "0"
        self.backend.save_state(state)

    def _selected_mode(self) -> PowerMode | None:
        for card in self.mode_cards:
            if card._selected:
                return card.mode
        return None

    def _select_mode(self, value: str) -> None:
        """Highlight the UI mode matching a hardware or UI profile value."""
        for card in self.mode_cards:
            mode = card.mode
            effective = self.backend.effective_profile_for(mode)
            matches = (
                mode.profile_value == value
                or value in mode.fallback_values
                or (effective is not None and effective == value)
            )
            card.set_selected(matches)

    def _on_mode_clicked(self) -> None:
        sender = self.sender()
        if not isinstance(sender, ModeCard):
            return
        # Deselect others
        for card in self.mode_cards:
            if card is not sender:
                card.set_selected(False)
        sender.set_selected(True)

        mode = sender.mode
        effective = self.backend.effective_profile_for(mode)
        if effective is None:
            self._show_error("Profile not supported", f"{mode.label} is not available on this system.")
            return

        ok, msg = self.backend.set_profile(effective)
        if ok:
            self.statusbar.showMessage(f"Power mode set to {mode.label} ({effective})")
            if self.auto_restore_check.isChecked():
                self._save_state()
        else:
            self._show_error("Failed to set power mode", msg)
            # If "custom" is rejected by the kernel, disable it to avoid confusion.
            if effective == "custom":
                sender.set_mode_enabled(False, "Not usable on this firmware")
            self._refresh_status()

    def _on_threshold_moved(self, value: int) -> None:
        self.threshold_value_label.setText(f"{value}%")

    def _apply_threshold(self) -> None:
        value = self.threshold_slider.value()
        ok, msg = self.backend.set_battery_threshold(value)
        if ok:
            self.statusbar.showMessage(msg)
            if self.auto_restore_check.isChecked():
                self._save_state()
        else:
            self._show_error("Failed to set battery threshold", msg)

    def _on_conservation_changed(self, state: int) -> None:
        enabled = state == QtCore.Qt.CheckState.Checked.value
        ok, msg = self.backend.set_conservation_mode(enabled)
        if ok:
            self.statusbar.showMessage(msg)
            if self.auto_restore_check.isChecked():
                self._save_state()
        else:
            self._show_error("Failed to set conservation mode", msg)
            # Revert checkbox without triggering signal loop.
            self.conservation_check.blockSignals(True)
            self.conservation_check.setChecked(not enabled)
            self.conservation_check.blockSignals(False)

    def _refresh_status(self) -> None:
        supported = self.backend.supported()
        if not any(supported.values()):
            self.compat_label.setText(
                "Warning: No supported power interfaces found. "
                "Make sure you are running this on a compatible Lenovo LOQ/IdeaPad system."
            )
            self.compat_label.setVisible(True)
        elif not all(supported.values()):
            missing = [k for k, v in supported.items() if not v]
            self.compat_label.setText(
                "Partial support: the following features are unavailable: "
                + ", ".join(missing)
            )
            self.compat_label.setVisible(True)
        else:
            self.compat_label.setVisible(False)

        # Read current values from hardware
        current_profile = self.backend.get_current_profile()
        if current_profile:
            self._select_mode(current_profile)
            label = self.backend.profile_label_for(current_profile) or current_profile
            self.statusbar.showMessage(f"Current profile: {label} ({current_profile})")

        threshold = self.backend.get_battery_threshold()
        if threshold is not None:
            self.threshold_slider.blockSignals(True)
            self.threshold_slider.setValue(threshold)
            self.threshold_slider.blockSignals(False)
            self.threshold_value_label.setText(f"{threshold}%")

        conservation = self.backend.get_conservation_mode()
        if conservation is not None:
            self.conservation_check.blockSignals(True)
            self.conservation_check.setChecked(conservation)
            self.conservation_check.blockSignals(False)

        # Battery threshold visibility
        if self.backend.battery_threshold_path is None:
            self.threshold_card.setVisible(False)
            self.threshold_unsupported_label.setVisible(True)
        else:
            self.threshold_card.setVisible(True)
            self.threshold_unsupported_label.setVisible(False)

        # Conservation mode availability
        if self.backend.conservation_mode_path is None:
            self.conservation_check.setEnabled(False)

        # Disable profile cards if platform_profile is unavailable
        if self.backend.platform_profile_path is None:
            for card in self.mode_cards:
                card.set_mode_enabled(False, "Not available on this system")

        # Start sensor timer if not already running
        if not hasattr(self, "sensor_timer"):
            self.sensor_timer = QtCore.QTimer(self)
            self.sensor_timer.timeout.connect(self._refresh_sensors)
            self.sensor_timer.start(2000)
            self._refresh_sensors()

    def _refresh_sensors(self) -> None:
        try:
            snapshot = self.sensor_monitor.read_all()
        except Exception as exc:
            self.cpu_card.set_value("Error")
            self.gpu_card.set_value("Error")
            self.fan_card.set_value(str(exc))
            self.other_card.set_value("--")
            return

        if snapshot.cpu_temp:
            self.cpu_card.set_value(f"{snapshot.cpu_temp.value:.1f} {snapshot.cpu_temp.unit}")
        else:
            self.cpu_card.set_value("Not available")

        if snapshot.gpu_temp:
            self.gpu_card.set_value(f"{snapshot.gpu_temp.value:.1f} {snapshot.gpu_temp.unit}")
        else:
            self.gpu_card.set_value("Not available")

        if snapshot.fan_speeds:
            self.fan_card.set_value(
                "\n".join(f"{s.value:.0f} {s.unit}" for s in snapshot.fan_speeds)
            )
        else:
            self.fan_card.set_value("Not available")

        if snapshot.other_temps:
            self.other_card.set_value(
                "\n".join(f"{s.name}: {s.value:.1f}{s.unit}" for s in snapshot.other_temps[:4])
            )
        else:
            self.other_card.set_value("--")

    def _show_error(self, title: str, message: str) -> None:
        QtWidgets.QMessageBox.critical(self, title, message)


class TrayApplication(QtWidgets.QApplication):
    """Optional system tray wrapper."""

    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.setApplicationName("LOQ Power Manager")
        self.setApplicationDisplayName("LOQ Power Manager")
        self.setDesktopFileName("loq-power-manager")

        self.backend = PowerBackend()
        self.window = MainWindow(self.backend)

        self.tray = QtWidgets.QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon
        ))
        self.tray.setToolTip("LOQ Power Manager")

        menu = QtWidgets.QMenu()
        show_action = menu.addAction("Open")
        show_action.triggered.connect(self.window.show)
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)

        self.tray.show()

    def _tray_activated(self, reason: QtWidgets.QSystemTrayIcon.ActivationReason) -> None:
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger:
            if self.window.isVisible():
                self.window.hide()
            else:
                self.window.show()
                self.window.raise_()
                self.window.activateWindow()


def restore_from_state() -> None:
    """Called at login by autostart to re-apply saved settings."""
    backend = PowerBackend()
    state = backend.load_saved_state()
    if state.get("auto_restore") != "1":
        return
    if "profile" in state and backend.platform_profile_path:
        backend.set_profile(state["profile"])
    if "threshold" in state and backend.battery_threshold_path:
        try:
            backend.set_battery_threshold(int(state["threshold"]))
        except ValueError:
            pass
    if "conservation" in state and backend.conservation_mode_path:
        backend.set_conservation_mode(state["conservation"] == "1")


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--restore":
        restore_from_state()
        return 0

    app = TrayApplication(sys.argv)
    app.window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
