"""Minimal MOVE Overview Flask app — runs locally on the Move device.

Usage:
  python app.py          # production mode (reads /data/UserData on Move)
  python app.py --mock   # mock mode for local testing on Mac
"""
import sys
from flask import Flask, render_template, jsonify
import os

import services.move_connection as mc
from services.bundle_parser import parse_bundle
from utils.camelot import keyToCamelot

MOCK = '--mock' in sys.argv

app = Flask(__name__)


def _mock_data():
    """Return realistic fake data for local testing."""
    return {
        'sets': [
            {'name': 'Set 1 - 90bpm AMin',    'path': '/mock/1', 'uuid': 'uuid-1', 'modified': 1747000000, 'bpm': 90,  'key': 'A',  'mode': 'minor', 'camelot': '8A', 'slot': 0,  'xattr_color': 19},
            {'name': 'Set 2 - 120bpm CMaj',   'path': '/mock/2', 'uuid': 'uuid-2', 'modified': 1747100000, 'bpm': 120, 'key': 'C',  'mode': 'major', 'camelot': '8B', 'slot': 1,  'xattr_color': 7},
            {'name': 'Set 3 - 140bpm DMin',   'path': '/mock/3', 'uuid': 'uuid-3', 'modified': 1747200000, 'bpm': 140, 'key': 'D',  'mode': 'minor', 'camelot': '7A', 'slot': 2,  'xattr_color': 2},
            {'name': 'Set 4 - 95bpm FMaj',    'path': '/mock/4', 'uuid': 'uuid-4', 'modified': 1747300000, 'bpm': 95,  'key': 'F',  'mode': 'major', 'camelot': '7B', 'slot': 3,  'xattr_color': 9},
            {'name': 'Set 5 - 170bpm DbMin',  'path': '/mock/5', 'uuid': 'uuid-5', 'modified': 1747400000, 'bpm': 170, 'key': 'Db', 'mode': 'minor', 'camelot': '12A','slot': 8,  'xattr_color': 17},
            {'name': 'Set 6 - 130bpm GMin',   'path': '/mock/6', 'uuid': 'uuid-6', 'modified': 1747500000, 'bpm': 130, 'key': 'G',  'mode': 'minor', 'camelot': '6A', 'slot': 9,  'xattr_color': 1},
            {'name': 'Set 7 - 110bpm EbMaj',  'path': '/mock/7', 'uuid': 'uuid-7', 'modified': 1747600000, 'bpm': 110, 'key': 'Eb', 'mode': 'major', 'camelot': '5B', 'slot': 16, 'xattr_color': 12},
            {'name': 'Set 8 - 85bpm BbMin',   'path': '/mock/8', 'uuid': 'uuid-8', 'modified': 1747700000, 'bpm': 85,  'key': 'Bb', 'mode': 'minor', 'camelot': '3A', 'slot': 17, 'xattr_color': 24},
        ],
        'disk': {'total_gb': 50.0, 'used_gb': 18.3, 'free_gb': 31.7, 'percent_used': 37},
        'total_sets': 8,
        'current_slot': 0,
    }


def get_sets_data():
    """Fetch all sets with metadata from the local filesystem."""
    if MOCK:
        return _mock_data()
    try:
        raw_sets = mc.list_sets()
        disk = mc.get_disk_usage()

        uuid_paths = [f"{mc.SETS_ROOT}/{s['uuid']}" for s in raw_sets]
        pad_positions = mc.get_pad_positions(uuid_paths)
        current_slot = mc.get_current_song_index()

        sets_data = []
        for s in raw_sets:
            uuid_path = f"{mc.SETS_ROOT}/{s['uuid']}"
            pad_info = pad_positions.get(uuid_path, {})

            entry = {
                'name': s['name'],
                'path': s['path'],
                'uuid': s['uuid'],
                'modified': s['modified'],
                'bpm': None,
                'key': None,
                'mode': None,
                'camelot': None,
                'slot': pad_info.get('slot'),
                'xattr_color': pad_info.get('xattr_color'),
            }

            try:
                abl = mc.read_song_abl(s['path'])
                bundle = parse_bundle(abl, s['name'])
                entry['bpm'] = bundle.bpm
                entry['key'] = bundle.key
                entry['mode'] = bundle.scale
                if bundle.key and bundle.scale:
                    entry['camelot'] = keyToCamelot(bundle.key, bundle.scale)
            except Exception:
                pass

            sets_data.append(entry)

        return {
            'sets': sets_data,
            'disk': disk,
            'total_sets': len(sets_data),
            'current_slot': current_slot,
        }
    except Exception as e:
        return {'error': str(e)}

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

def get_system_stats():
    """Read CPU and memory stats from /proc."""
    stats = {}
    try:
        with open('/proc/loadavg') as f:
            parts = f.read().split()
        stats['load_1']  = float(parts[0])
        stats['load_5']  = float(parts[1])
        stats['load_15'] = float(parts[2])
    except Exception:
        pass
    try:
        meminfo = {}
        with open('/proc/meminfo') as f:
            for line in f:
                key, val = line.split(':', 1)
                meminfo[key.strip()] = int(val.strip().split()[0])
        total_kb = meminfo.get('MemTotal', 0)
        avail_kb = meminfo.get('MemAvailable', meminfo.get('MemFree', 0))
        used_kb  = total_kb - avail_kb
        stats['mem_total_mb'] = round(total_kb / 1024)
        stats['mem_used_mb']  = round(used_kb  / 1024)
        stats['mem_pct']      = round(used_kb / total_kb * 100) if total_kb else 0
    except Exception:
        pass
    try:
        stats['cpu_count'] = os.cpu_count() or 1
    except Exception:
        pass
    return stats


@app.route('/api/system')
def api_system():
    """Lightweight endpoint returning CPU load and memory usage."""
    return jsonify(get_system_stats())


@app.route('/api/active-slot')
def api_active_slot():
    """Lightweight endpoint returning only the current active pad slot."""
    return jsonify({'current_slot': mc.get_current_song_index()})

@app.route('/api/data')
def api_data():
    """API endpoint for sets data."""
    data = get_sets_data()
    return jsonify(data)

if __name__ == '__main__':
    # Run on port 808 (different from Schwung's 7700)
    app.run(host='0.0.0.0', port=808, debug=True)
