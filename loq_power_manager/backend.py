"""
Hardware backend for Lenovo LOQ / IdeaPad / Legion power management.

Detects and controls:
  - ACPI platform_profile (power modes)
  - Battery charge control end threshold
  - Lenovo conservation mode

All privileged writes are delegated to small helper scripts executed via pkexec.
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple


@dataclass(frozen=True)
class PowerMode:
    label: str
    icon: str
    profile_value: str
    description: str
    # Alternative names the same concept may have on different firmwares.
    fallback_values: Tuple[str, ...] = ()


# Mapping from friendly UI names to the values accepted by platform_profile.
# If a value is not available on the machine, the UI can fall back.
DEFAULT_MODES: List[PowerMode] = [
    PowerMode("Silent", "audio-volume-muted", "quiet",
              "Minimum fan noise and power consumption",
              fallback_values=("low-power", "quiet")),
    PowerMode("Balanced", "preferences-system-power", "balanced",
              "Everyday performance and battery life"),
    PowerMode("Gaming", "input-gaming", "performance",
              "Maximum CPU/GPU performance",
              fallback_values=("performance", "max-power")),
    PowerMode("Custom", "document-edit", "custom",
              "Use the platform 'custom' profile (may require BIOS/firmware support)",
              fallback_values=("custom",)),
]


class PowerBackend:
    """Detect available sysfs interfaces and read/write settings."""

    def __init__(self, helpers_dir: Optional[Path] = None) -> None:
        if helpers_dir is not None:
            self.helpers_dir = Path(helpers_dir)
        else:
            # Helpers may be next to the source package or in a system directory.
            candidates = [
                Path(__file__).resolve().parent.parent / "helpers",
                Path("/usr/lib/loq-power-manager/helpers"),
                Path("/usr/local/lib/loq-power-manager/helpers"),
                Path("/usr/share/loq-power-manager/helpers"),
            ]
            self.helpers_dir = candidates[0]
            for c in candidates:
                if (c / "set_power_profile.sh").exists():
                    self.helpers_dir = c
                    break

        self.platform_profile_path: Optional[Path] = None
        self.platform_profile_choices_path: Optional[Path] = None
        self.battery_threshold_path: Optional[Path] = None
        self.conservation_mode_path: Optional[Path] = None

        self._detect()

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------
    def _detect(self) -> None:
        # platform_profile
        pp = Path("/sys/firmware/acpi/platform_profile")
        if pp.exists():
            self.platform_profile_path = pp
            ppc = Path("/sys/firmware/acpi/platform_profile_choices")
            if ppc.exists():
                self.platform_profile_choices_path = ppc

        # Battery charge threshold - several possible paths
        candidates = [
            "/sys/class/power_supply/BAT0/charge_control_end_threshold",
            "/sys/class/power_supply/BAT1/charge_control_end_threshold",
        ]
        # Add any Lenovo platform specific paths
        candidates.extend(glob.glob("/sys/devices/platform/*lenovo*/charge_control_end_threshold"))
        candidates.extend(glob.glob("/sys/bus/platform/drivers/ideapad_acpi/*:*/charge_control_end_threshold"))

        for c in candidates:
            p = Path(c)
            if p.exists():
                self.battery_threshold_path = p
                break

        # Conservation mode (IdeaPad / LOQ)
        cm_candidates = []
        cm_candidates.extend(glob.glob("/sys/bus/platform/drivers/ideapad_acpi/*:*/conservation_mode"))
        cm_candidates.extend(glob.glob("/sys/devices/platform/VPC*/conservation_mode"))
        cm_candidates.extend(glob.glob("/sys/devices/pci*/*/PNP0C09:00/VPC*/conservation_mode"))
        for c in cm_candidates:
            p = Path(c)
            if p.exists():
                self.conservation_mode_path = p
                break

    def supported(self) -> dict:
        """Return a dict describing which features are available."""
        return {
            "platform_profile": self.platform_profile_path is not None,
            "battery_threshold": self.battery_threshold_path is not None,
            "conservation_mode": self.conservation_mode_path is not None,
        }

    def is_compatible(self) -> bool:
        return any(self.supported().values())

    # ------------------------------------------------------------------
    # Power profile
    # ------------------------------------------------------------------
    def available_profile_values(self) -> List[str]:
        if self.platform_profile_choices_path:
            try:
                return self.platform_profile_choices_path.read_text().strip().split()
            except Exception:
                pass
        return [m.profile_value for m in DEFAULT_MODES]

    def effective_profile_for(self, mode: PowerMode) -> Optional[str]:
        """Return the hardware profile value that best matches a UI mode."""
        allowed = self.available_profile_values()
        for value in (mode.profile_value,) + mode.fallback_values:
            if value in allowed:
                return value
        return None

    def profile_label_for(self, value: str) -> Optional[str]:
        """Return the UI label for a hardware profile value, if any."""
        for mode in DEFAULT_MODES:
            if value == mode.profile_value or value in mode.fallback_values:
                return mode.label
        return None

    def get_current_profile(self) -> Optional[str]:
        if not self.platform_profile_path:
            return None
        try:
            return self.platform_profile_path.read_text().strip()
        except Exception:
            return None

    def set_profile(self, value: str) -> Tuple[bool, str]:
        if not self.platform_profile_path:
            return False, "platform_profile is not available on this system"

        # Validate against allowed choices if we know them.
        allowed = self.available_profile_values()
        if allowed and value not in allowed:
            return False, f"Profile '{value}' not in allowed choices: {allowed}"

        return self._run_helper(
            "set_power_profile.sh",
            str(self.platform_profile_path),
            value,
        )

    # ------------------------------------------------------------------
    # Battery threshold
    # ------------------------------------------------------------------
    def get_battery_threshold(self) -> Optional[int]:
        if not self.battery_threshold_path:
            return None
        try:
            text = self.battery_threshold_path.read_text().strip()
            return int(text)
        except Exception:
            return None

    def set_battery_threshold(self, value: int) -> Tuple[bool, str]:
        if not self.battery_threshold_path:
            return False, "Battery charge threshold is not available"
        if not 20 <= value <= 100:
            return False, "Threshold must be between 20 and 100"

        return self._run_helper(
            "set_battery_threshold.sh",
            str(self.battery_threshold_path),
            str(value),
        )

    # ------------------------------------------------------------------
    # Conservation mode
    # ------------------------------------------------------------------
    def get_conservation_mode(self) -> Optional[bool]:
        if not self.conservation_mode_path:
            return None
        try:
            text = self.conservation_mode_path.read_text().strip()
            return text == "1"
        except Exception:
            return None

    def set_conservation_mode(self, enabled: bool) -> Tuple[bool, str]:
        if not self.conservation_mode_path:
            return False, "Conservation mode is not available"
        value = "1" if enabled else "0"
        return self._run_helper(
            "set_conservation_mode.sh",
            str(self.conservation_mode_path),
            value,
        )

    # ------------------------------------------------------------------
    # Privilege helper
    # ------------------------------------------------------------------
    def _run_helper(self, script: str, *args: str) -> Tuple[bool, str]:
        script_path = self.helpers_dir / script
        if not script_path.exists():
            return False, f"Helper script not found: {script_path}"

        cmd = ["pkexec", str(script_path), *args]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return True, result.stdout.strip() or "OK"
            else:
                err = result.stderr.strip()
                if "not authorized" in err.lower() or "polkit" in err.lower():
                    return False, "Authorization cancelled or denied."
                return False, err or f"Helper failed with code {result.returncode}"
        except subprocess.TimeoutExpired:
            return False, "Operation timed out"
        except FileNotFoundError:
            return False, "pkexec not found. Please install polkit."
        except Exception as e:
            return False, str(e)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def state_file(self) -> Path:
        config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        app_dir = config_dir / "loq-power-manager"
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir / "state.conf"

    def load_saved_state(self) -> dict:
        state: dict = {}
        sf = self.state_file()
        if not sf.exists():
            return state
        try:
            for line in sf.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                state[key.strip()] = value.strip()
        except Exception:
            pass
        return state

    def save_state(self, state: dict) -> None:
        sf = self.state_file()
        lines = ["# LOQ Power Manager saved state\n"]
        for key, value in state.items():
            lines.append(f"{key}={value}\n")
        try:
            sf.write_text("".join(lines))
        except Exception as e:
            print(f"Failed to save state: {e}")
