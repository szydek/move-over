"""Camelot wheel utilities for the backend — mirrors frontend/src/utils/camelot.js."""

from typing import Optional

KEY_TO_CAMELOT = {
    'Ab minor': '1A', 'G# minor': '1A',
    'B major':  '1B', 'Cb major': '1B',
    'Eb minor': '2A', 'D# minor': '2A',
    'F# major': '2B', 'Gb major': '2B',
    'Bb minor': '3A', 'A# minor': '3A',
    'Db major': '3B', 'C# major': '3B',
    'F minor':  '4A',
    'Ab major': '4B', 'G# major': '4B',
    'C minor':  '5A',
    'Eb major': '5B', 'D# major': '5B',
    'G minor':  '6A',
    'Bb major': '6B', 'A# major': '6B',
    'D minor':  '7A',
    'F major':  '7B',
    'A minor':  '8A',
    'C major':  '8B',
    'E minor':  '9A',
    'G major':  '9B',
    'B minor':  '10A', 'Cb minor': '10A',
    'D major':  '10B',
    'F# minor': '11A', 'Gb minor': '11A',
    'A major':  '11B',
    'Db minor': '12A', 'C# minor': '12A',
    'E major':  '12B',
}

FLAT_SLUGS  = {'Ab': 'Aflat', 'Bb': 'Bflat', 'Db': 'Dflat', 'Eb': 'Eflat', 'Gb': 'Gflat'}
SHARP_SLUGS = {'F#': 'Fsharp', 'G#': 'Gsharp', 'C#': 'Csharp', 'D#': 'Dsharp', 'A#': 'Asharp'}

# Maps Song.abl scale strings (after .lower()) → filename slug
MODE_SLUGS = {
    'major': 'Maj', 'minor': 'Min',
    'dorian': 'Dor', 'phrygian': 'Phr', 'lydian': 'Lyd',
    'mixolydian': 'Mix', 'locrian': 'Loc',
    'harmonicminor': 'HMin', 'harmonic minor': 'HMin',
    'melodicminor': 'MMin', 'melodic minor': 'MMin',
    'majorpentatonic': 'PenMaj', 'major pentatonic': 'PenMaj',
    'minorpentatonic': 'PenMin', 'minor pentatonic': 'PenMin',
    'blues': 'Blues',
    'wholetone': 'WT', 'whole tone': 'WT',
    'diminished': 'Dim', 'augmented': 'Aug',
}


def keyToCamelot(key: str, mode: str) -> Optional[str]:  # noqa: N802
    return KEY_TO_CAMELOT.get(f'{key} {mode}')


def keyToSlug(key: str, mode: str) -> str:  # noqa: N802
    key_part = FLAT_SLUGS.get(key) or SHARP_SLUGS.get(key) or key
    mode_part = MODE_SLUGS.get(mode, mode.capitalize() if mode else 'Maj')
    return f'{key_part}{mode_part}'
