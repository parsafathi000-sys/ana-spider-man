"""Generate short looping music tracks (WAV) for the Spider Panel "music on open" feature.

No external deps: uses only the stdlib `wave` + `struct` + `math`. Each track is a
few seconds of a gentle sine-based melody with a soft attack/decay envelope so it
loops without a click. Browsers play WAV natively via the HTML5 <audio> element.

Run:  python3 _generate_music.py
"""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAMPLE_RATE = 44100


def _note(freq: float, dur: float, vol: float = 0.25) -> list[int]:
    """One note with a soft attack/decay envelope -> 16-bit PCM samples."""
    n = int(SAMPLE_RATE * dur)
    attack = int(SAMPLE_RATE * 0.02)
    release = int(SAMPLE_RATE * 0.08)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = 1.0
        if i < attack:
            env = i / attack
        elif i > n - release:
            env = max(0.0, (n - i) / release)
        # slight vibrato for warmth
        ph = 2 * math.pi * freq * t + 0.004 * math.sin(2 * math.pi * 5 * t)
        s = math.sin(ph) * env * vol
        # add a quiet harmonic for body
        s += 0.4 * math.sin(2 * math.pi * freq * 2 * t) * env * vol * 0.3
        samples.append(int(max(-1.0, min(1.0, s)) * 32767))
    return samples


def _render(notes: list[tuple[float, float]], vol: float = 0.25) -> bytes:
    frames: list[int] = []
    for freq, dur in notes:
        frames.extend(_note(freq, dur, vol))
    return b"".join(struct.pack("<h", s) for s in frames)


def _write(name: str, pcm: bytes) -> None:
    path = HERE / name
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)
    print("wrote", path.name, f"({len(pcm)} bytes)")


# A few recognizable moods. Frequencies in Hz (equal temperament).
def _build_tracks() -> list[tuple[str, bytes]]:
    A4 = 440.0
    notes = {
        "C4": A4 * 2 ** (-9 / 12), "D4": A4 * 2 ** (-7 / 12),
        "E4": A4 * 2 ** (-5 / 12), "F4": A4 * 2 ** (-4 / 12),
        "G4": A4 * 2 ** (-2 / 12), "A4": A4, "B4": A4 * 2 ** (2 / 12),
        "C5": A4 * 2 ** (3 / 12), "E5": A4 * 2 ** (7 / 12),
        "G3": A4 * 2 ** (-14 / 12), "C3": A4 * 2 ** (-21 / 12),
    }

    # 1) "neon-dawn" — bright rising arpeggio
    t1 = [(notes["C4"], 0.22), (notes["E4"], 0.22), (notes["G4"], 0.22),
          (notes["C5"], 0.30), (notes["G4"], 0.22), (notes["E4"], 0.22)]
    # 2) "midnight-protocol" — moody minor loop
    t2 = [(notes["A4"], 0.28), (notes["C5"], 0.24), (notes["E5"], 0.28),
          (notes["D4"], 0.30), (notes["A4"], 0.24), (notes["C5"], 0.24)]
    # 3) "web-spinner" — bouncy playful
    t3 = [(notes["G4"], 0.16), (notes["C5"], 0.16), (notes["E5"], 0.16),
          (notes["C5"], 0.16), (notes["G4"], 0.16), (notes["B4"], 0.16),
          (notes["D4"], 0.18)]
    # 4) "deep-link" — low calm pad with bass
    t4 = [(notes["C3"], 0.5), (notes["G3"], 0.5), (notes["C4"], 0.4),
          (notes["E4"], 0.4), (notes["G3"], 0.5), (notes["C3"], 0.5)]

    return [
        ("neon-dawn.wav", _render(t1, vol=0.28)),
        ("midnight-protocol.wav", _render(t2, vol=0.30)),
        ("web-spinner.wav", _render(t3, vol=0.24)),
        ("deep-link.wav", _render(t4, vol=0.34)),
    ]


def main() -> None:
    for name, pcm in _build_tracks():
        _write(name, pcm)
    # keep the generator itself out of the served listing (no audio extension)


if __name__ == "__main__":
    main()
