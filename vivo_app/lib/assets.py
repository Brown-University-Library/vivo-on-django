"""Asset helpers for static resources.

Provides small utilities for selecting randomized images to support
homepage parity with the legacy Rails implementation.
"""

from __future__ import annotations

import random
from pathlib import Path

from django.conf import settings


def get_random_background_relpath() -> str:
    """Return a random hero background path relative to the static root.

    Looks in each STATICFILES_DIRS entry under images/new-backgrounds/ and
    returns one randomized file with image extensions. Falls back to a safe
    placeholder if none are present.
    """
    candidates: list[str] = []
    exts = ('*.jpg', '*.jpeg', '*.png', '*.webp')
    for static_dir in getattr(settings, 'STATICFILES_DIRS', []):
        base = Path(static_dir) / 'images' / 'new-backgrounds'
        if base.exists():
            for pattern in exts:
                for fp in base.glob(pattern):
                    candidates.append(f'images/new-backgrounds/{fp.name}')
    if candidates:
        return random.choice(candidates)
    # Fallback image used earlier in CSS
    return 'images/vivo_blank_profile.jpg'
