"""Asset helpers for static resources.

Provides small utilities for selecting randomized images to support
homepage parity with the legacy Rails implementation.
"""

from __future__ import annotations

import random
from pathlib import Path

from django.conf import settings


def get_random_background_relpath() -> str:
    """
    Returns a random hero background path relative to the static root.

    Called by: home_index()
    """
    candidates: list[str] = []
    exts = ('*.jpg', '*.jpeg', '*.png', '*.webp')
    base = Path(settings.BASE_DIR) / 'vivo_app' / 'static' / 'images' / 'new-backgrounds'
    if base.exists():
        for pattern in exts:
            for fp in base.glob(pattern):
                candidates.append(f'images/new-backgrounds/{fp.name}')
    if candidates:
        return random.choice(candidates)
    return 'images/vivo_blank_profile.jpg'
