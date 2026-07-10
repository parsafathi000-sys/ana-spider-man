"""QR code generation for VLESS links.

Spider's requirements already include qrcode[pil]; the bot reuses the same lib
so a config link can be rendered as a scannable PNG for the user.
"""
import io
from pathlib import Path

import qrcode


def make_qr(vless_link: str, out_dir: Path) -> Path:
    """Render ``vless_link`` to a PNG and return its path.

    Uses a deterministic filename derived from the link so repeated calls for
    the same config are idempotent (no QR spam in the data dir).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = abs(hash(vless_link))
    path = out_dir / f"qr_{safe}.png"
    if path.exists():
        return path
    img = qrcode.make(vless_link)
    img.save(path)
    return path
