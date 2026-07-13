"""Settings + music router.

Settings are stored in the generic `Setting` key/value table. The frontend
reads them to render toggles (e.g. "play music when panel opens") and writes
changes back here. Music files are served from the static `/musics` mount and
listed by `/api/music/list` so the client can pick a random file.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_admin
from app.database import get_db
from app.users.models import AdminUser, Setting

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Keys the panel cares about. New keys can be added freely; this is the allow-list
# the frontend exposes as toggles so arbitrary rows don't leak into the UI.
KNOWN_KEYS = (
    "music_enabled",    # "1" = background music on
    "music_volume",     # "0.0".."1.0" player volume
    "music_random",     # "1" = pick a random track on open
    "music_track",      # selected file name (empty = first/random)
)


# ---------------------------------------------------------------------------
# Music
# ---------------------------------------------------------------------------
_MUSICS_DIR = Path(__file__).resolve().parent.parent / "static" / "musics"

_AUDIO_EXT = (".mp3", ".ogg", ".wav", ".m4a", ".webm", ".aac", ".flac")


def list_music_files() -> list[str]:
    if not _MUSICS_DIR.is_dir():
        return []
    out = []
    for p in sorted(_MUSICS_DIR.iterdir()):
        if p.is_file() and p.suffix.lower() in _AUDIO_EXT:
            out.append(p.name)
    return out


@router.get("/music/list")
async def music_list(_: AdminUser = Depends(get_current_admin)):
    return {"files": list_music_files(), "url_prefix": "/musics/"}


# ---------------------------------------------------------------------------
# Settings key/value
# ---------------------------------------------------------------------------
class SettingSet(BaseModel):
    key: str
    value: str


def _normalize(key: str, value: str) -> str:
    """Validate + coerce a setting value before persisting."""
    if key == "music_volume":
        try:
            v = max(0, min(100, int(float(value))))
        except (ValueError, TypeError):
            v = 70
        return str(v)
    if key in ("music_enabled", "music_random"):
        # accept "1"/"true"/"on" as enabled, else "0"
        return "1" if str(value).strip().lower() in ("1", "true", "on", "yes") else "0"
    if key == "music_track":
        # Only allow a track name that actually exists in the music dir.
        if value and value not in list_music_files():
            return ""
        return value
    return value


@router.get("")
async def get_settings(_: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Setting))
    rows = res.scalars().all()
    data = {r.key: r.value for r in rows}
    # ensure known keys always reported (default = off / empty)
    for k in KNOWN_KEYS:
        data.setdefault(k, "")
    files = list_music_files()
    # Volume as integer percent (default 70).
    vol = 70
    try:
        vol = max(0, min(100, int(float(data["music_volume"]))))
    except (ValueError, TypeError):
        vol = 70
    return {
        "settings": data,
        "music": {
            "enabled": data["music_enabled"] == "1",
            "volume": vol,
            "random": data["music_random"] == "1",
            "track": data["music_track"],
            "files": files,
            "url_prefix": "/musics/",
        },
    }


@router.post("")
async def set_setting(
    payload: SettingSet,
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if payload.key not in KNOWN_KEYS:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=f"Unknown setting key: {payload.key}")
    value = _normalize(payload.key, payload.value)
    res = await db.execute(select(Setting).where(Setting.key == payload.key))
    row = res.scalar_one_or_none()
    if row is None:
        row = Setting(key=payload.key, value=value)
        db.add(row)
    else:
        row.value = value
    await db.commit()
    return {"ok": True, "key": payload.key, "value": value}
