"""Parse Ableton Move .ablbundle files to extract BPM, key, and scale.

.ablbundle is a ZIP archive containing Song.abl (JSON) and audio samples.
Song.abl schema: http://tech.ableton.com/schema/song/1.8.1/song.json

Older .als files (Ableton Live desktop) are gzip-compressed XML — handled as
a fallback for BPM only since they use a different schema without key/scale.
"""
import gzip
import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional

# MIDI root note 0–11 → note name (prefer flats to match Ableton Move display)
_ROOT_NOTE_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']


class BundleInfo:
    __slots__ = ('bpm', 'key', 'scale', 'set_number', 'color')

    def __init__(self, bpm=None, key=None, scale=None, set_number=None, color=None):
        self.bpm = bpm
        self.key = key
        self.scale = scale
        self.set_number = set_number
        self.color = color


def parse_bundle(data: bytes, filename: str = '') -> BundleInfo:
    """Parse an .ablbundle or .als file and return all available metadata."""
    info = BundleInfo(set_number=extract_set_number(filename))

    if zipfile.is_zipfile(io.BytesIO(data)):
        _parse_zip(data, info)
    elif data[:2] == b'\x1f\x8b':
        # Plain gzip .als (desktop Live format) — BPM only
        info.bpm = _bpm_from_gzip_als(data)
    elif data[:1] == b'{':
        # Unwrapped Song.abl JSON
        _parse_song_json(data, info)

    return info


def _parse_zip(data: bytes, info: BundleInfo):
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        # Move format: Song.abl (JSON)
        if 'Song.abl' in names:
            _parse_song_json(zf.read('Song.abl'), info)
        else:
            # Fallback: look for legacy .als inside ZIP
            als_names = sorted([n for n in names if n.endswith('.als')], key=lambda n: n.count('/'))
            if als_names:
                info.bpm = _bpm_from_gzip_als(zf.read(als_names[0]))


def _parse_song_json(raw: bytes, info: BundleInfo):
    try:
        song = json.loads(raw)
    except Exception:
        return

    if 'tempo' in song:
        try:
            info.bpm = float(song['tempo'])
        except (ValueError, TypeError):
            pass

    root_note = song.get('rootNote')
    scale = song.get('scale')

    if root_note is not None and scale:
        try:
            info.key = _ROOT_NOTE_NAMES[int(root_note) % 12]
            info.scale = scale.lower()  # normalize: "Minor" → "minor", "Major" → "major"
        except (ValueError, TypeError, IndexError):
            pass

    try:
        color = song.get('masterTrack', {}).get('color')
        if color is not None:
            info.color = int(color)
    except (ValueError, TypeError):
        pass


def _bpm_from_gzip_als(als_bytes: bytes) -> Optional[float]:
    try:
        xml_bytes = gzip.decompress(als_bytes)
        root = ET.fromstring(xml_bytes)
        tempo_el = root.find('.//Tempo/Manual')
        if tempo_el is not None:
            return float(tempo_el.attrib.get('Value', ''))
    except Exception:
        pass
    return None


# Keep old function name for backward compat with move.py router
def parse_bpm(data: bytes, filename: str = '') -> Optional[float]:
    return parse_bundle(data, filename).bpm


def extract_set_number(filename: str) -> Optional[int]:
    match = re.search(r'Set\s*(\d+)', filename, re.IGNORECASE)
    return int(match.group(1)) if match else None
