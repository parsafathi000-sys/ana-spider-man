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
    "music_on_open",  # "1" = play a random track when the panel opens
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


@router.get("")
async def get_settings(_: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Setting))
    rows = res.scalars().all()
    data = {r.key: r.value for r in rows}
    # ensure known keys always reported (default = off)
    for k in KNOWN_KEYS:
        data.setdefault(k, "")
    return data


@router.post("")
async def set_setting(
    payload: SettingSet,
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if payload.key not in KNOWN_KEYS:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=f"Unknown setting key: {payload.key}")
    res = await db.execute(select(Setting).where(Setting.key == payload.key))
    row = res.scalar_one_or_none()
    if row is None:
        row = Setting(key=payload.key, value=payload.value)
        db.add(row)
    else:
        row.value = payload.value
    await db.commit()
    return {"ok": True, "key": payload.key, "value": payload.value}
