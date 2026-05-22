"""Local filesystem access to Move's set data.

Running directly on the Move device — no SSH/SFTP needed.
Reads sets from the local filesystem at /data/UserData/UserLibrary/Sets/.
"""
import json
import os
import re
import shutil
from pathlib import Path
from typing import Optional

from config import settings

SETS_ROOT = settings.move_sets_root
SETTINGS_JSON = '/data/UserData/settings/Settings.json'


def list_sets() -> list:
    """List all sets from the local filesystem."""
    results = []
    try:
        sets_root = Path(SETS_ROOT)
        for uuid_dir in sets_root.iterdir():
            if not uuid_dir.is_dir():
                continue
            children = [d for d in uuid_dir.iterdir() if d.is_dir()]
            if not children:
                continue
            set_dir = children[0]
            results.append({
                'name': set_dir.name,
                'path': str(set_dir),
                'uuid': uuid_dir.name,
                'modified': uuid_dir.stat().st_mtime,
            })
    except Exception:
        pass

    def _sort_key(s):
        m = re.search(r'\d+', s['name'])
        return int(m.group()) if m else 9999

    return sorted(results, key=_sort_key)


def read_song_abl(set_path: str) -> bytes:
    """Read Song.abl from a set directory."""
    with open(f'{set_path}/Song.abl', 'rb') as f:
        return f.read()


def get_disk_usage() -> Optional[dict]:
    """Return disk usage for the user data partition using shutil."""
    try:
        usage = shutil.disk_usage('/data/UserData')
        total_kb = usage.total // 1024
        used_kb  = usage.used  // 1024
        free_kb  = usage.free  // 1024
        pct      = round(usage.used / usage.total * 100)
        return {
            'total_gb':     round(total_kb / 1024 / 1024, 1),
            'used_gb':      round(used_kb  / 1024 / 1024, 1),
            'free_gb':      round(free_kb  / 1024 / 1024, 1),
            'percent_used': pct,
        }
    except Exception:
        return None


def _read_xattr(path: str, attr_name: str) -> Optional[str]:
    """Read a single xattr using os.getxattr() (Linux stdlib, no subprocess)."""
    try:
        raw = os.getxattr(path, attr_name)
        return raw.decode('utf-8', errors='replace').strip() or None
    except Exception:
        return None


def get_pad_positions(uuid_paths: list) -> dict:
    """Return {uuid_path: {slot, xattr_color}} for each UUID dir."""
    result = {}
    for path in uuid_paths:
        slot_val  = _read_xattr(path, 'user.song-index')
        color_val = _read_xattr(path, 'user.song-color')
        try:
            slot = int(slot_val) if slot_val is not None else None
        except (ValueError, TypeError):
            slot = None
        try:
            xattr_color = int(color_val) if color_val is not None else None
        except (ValueError, TypeError):
            xattr_color = None
        result[path] = {'slot': slot, 'xattr_color': xattr_color}
    return result


def get_current_song_index() -> Optional[int]:
    """Read currentSongIndex (0-31) from Move's Settings.json."""
    try:
        with open(SETTINGS_JSON, 'r') as f:
            data = json.load(f)
        val = data.get('currentSongIndex')
        return int(val) if val is not None else None
    except Exception:
        return None
