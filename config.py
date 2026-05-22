"""Configuration for MOVE Overview POC."""
import os
from pathlib import Path

class Settings:
    move_host: str = os.getenv('MOVE_HOST', 'move.local')
    move_ssh_key_path: Path = Path.home() / '.ssh' / 'move_toolkit_rsa'
    move_sets_root: str = '/data/UserData/UserLibrary/Sets'

settings = Settings()
