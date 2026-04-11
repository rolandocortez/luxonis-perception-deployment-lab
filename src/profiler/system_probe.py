from __future__ import annotations

import platform


def get_system_info() -> dict[str, str]:
    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "processor": platform.processor(),
        "machine": platform.machine(),
    }