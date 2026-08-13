"""
Read CPU/GPU temperatures and fan speeds from /sys/class/hwmon.

This is intentionally read-only. Fan control is not implemented because
Lenovo LOQ/IdeaPad laptops do not expose a standard sysfs fan-control
interface; that typically requires the community LenovoLegionLinux driver.
"""

from __future__ import annotations

import glob
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SensorReading:
    name: str
    value: float
    unit: str


@dataclass
class SensorSnapshot:
    cpu_temp: Optional[SensorReading] = None
    gpu_temp: Optional[SensorReading] = None
    fan_speeds: List[SensorReading] = field(default_factory=list)
    other_temps: List[SensorReading] = field(default_factory=list)


class SensorMonitor:
    """Discover and read hwmon sensors."""

    HWMON_BASE = Path("/sys/class/hwmon")

    # Mapping of hwmon driver names to friendly categories.
    CPU_DRIVERS = {"k10temp", "coretemp", "zenpower"}
    GPU_DRIVERS = {"amdgpu", "nvidia", "nouveau", "radeon", "i915"}

    def __init__(self) -> None:
        pass

    def read_all(self) -> SensorSnapshot:
        snapshot = SensorSnapshot()
        if not self.HWMON_BASE.exists():
            return snapshot

        for hwmon_dir in sorted(self.HWMON_BASE.glob("hwmon*")):
            name_file = hwmon_dir / "name"
            if not name_file.exists():
                continue
            driver = name_file.read_text().strip()

            temps = self._read_temps(hwmon_dir, driver)
            fans = self._read_fans(hwmon_dir, driver)

            if driver in self.CPU_DRIVERS:
                # Prefer the first/main temperature on the CPU driver.
                if temps:
                    snapshot.cpu_temp = temps[0]
            elif driver in self.GPU_DRIVERS:
                if temps:
                    snapshot.gpu_temp = temps[0]
            elif driver in {"acpi_fan", "thinkpad", "asus", "dell_smm"}:
                snapshot.fan_speeds.extend(fans)
            else:
                # Keep fan readings from any driver as fallback.
                snapshot.fan_speeds.extend(fans)
                # Store other temperatures (e.g. NVMe, ACPI thermal zone).
                snapshot.other_temps.extend(temps)

        return snapshot

    def _read_temps(self, hwmon_dir: Path, driver: str) -> List[SensorReading]:
        readings: List[SensorReading] = []
        inputs = sorted(hwmon_dir.glob("temp*_input"))
        for inp in inputs:
            try:
                raw = int(inp.read_text().strip())
                celsius = raw / 1000.0
            except (ValueError, OSError):
                continue

            label_file = inp.with_name(inp.name.replace("_input", "_label"))
            label = label_file.read_text().strip() if label_file.exists() else "Temp"
            name = f"{driver} {label}"
            readings.append(SensorReading(name, celsius, "°C"))
        return readings

    def _read_fans(self, hwmon_dir: Path, driver: str) -> List[SensorReading]:
        readings: List[SensorReading] = []
        inputs = sorted(hwmon_dir.glob("fan*_input"))
        for inp in inputs:
            try:
                rpm = int(inp.read_text().strip())
            except (ValueError, OSError):
                continue
            label_file = inp.with_name(inp.name.replace("_input", "_label"))
            label = label_file.read_text().strip() if label_file.exists() else "Fan"
            name = f"{driver} {label}"
            readings.append(SensorReading(name, float(rpm), "RPM"))
        return readings
