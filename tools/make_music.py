"""Original background music for the showcase video, synthesised from scratch (no samples, no licences needed).

Chord changes land on the video's scene changes. Run, then mix into the video:

    python tools/make_music.py tools/kf-music.wav
    ffmpeg -i static/assets/video/kf-services.mp4 -i tools/kf-music.wav -map 0:v -map 1:a -c:v copy \
           -c:a aac -b:a 128k -shortest -movflags +faststart out.mp4
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

SR = 44100
LENGTH = 34.08  # seconds, same as the video

# Scene start times in the video (intro, 5 cleaning scenes, real estate card, 4 real estate scenes, outro).
SEGMENTS = [
    # start, chord, drums, arpeggio
    (0.0, "D", False, False),    # intro: logo
    (3.4, "D", True, True),      # cleaning
    (6.0, "A", True, True),      # post-construction
    (8.6, "Bm", True, True),     # fumigation
    (11.2, "G", True, True),     # garbage
    (13.8, "D", True, True),     # landscaping
    (16.4, "Em", False, True),   # "Real Estate Services" card: drums drop out
    (18.2, "Bm", True, True),    # property management
    (20.8, "G", True, True),     # facilities
    (23.4, "D", True, True),     # rent collection
    (26.0, "A", True, True),     # land & valuation
    (28.6, "G", True, False),    # outro, part 1
    (31.2, "D", False, False),   # outro: resolve and fade
]
CHORDS = {  # pad voicing (MIDI notes), bass note
    "D": ([50, 54, 57, 62], 38),
    "A": ([49, 52, 57, 61], 45),
    "Bm": ([50, 54, 59, 62], 47),
    "G": ([50, 55, 59, 62], 43),
    "Em": ([52, 55, 59, 64], 40),
}
BEAT = 0.65  # 92 bpm: four beats per 2.6 s scene

# Chord and arrangement per scene when the timeline comes from build_showcase.py:
# intro, 5 cleaning scenes, real estate card, 4 real estate scenes, outro (split in two).
PLAN = [("D", False, False), ("D", True, True), ("A", True, True), ("Bm", True, True), ("G", True, True),
        ("D", True, True), ("Em", False, True), ("Bm", True, True), ("G", True, True), ("D", True, True),
        ("A", True, True)]


def segments_from_timeline(starts, duration):
    """Map scene start times onto the chord plan; the outro holds G, then resolves to D."""
    segments = [(s, *PLAN[i]) for i, s in enumerate(starts[:-1])]
    outro = starts[-1]
    segments += [(outro, "G", True, False), (outro + (duration - outro) / 2, "D", False, False)]
    return segments


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def tone(freq, dur, harmonics=6, rolloff=1.5, detune=0.0):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for n in range(1, harmonics + 1):
        out += np.sin(2 * np.pi * freq * n * (1 + detune) * t) / n ** rolloff
    return out


def env_adsr(n, attack, release):
    e = np.ones(n)
    a, r = int(attack * SR), int(release * SR)
    e[:a] = np.linspace(0, 1, a) if a else 1
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def pluck_env(n, decay):
    return np.exp(-np.arange(n) / SR / decay)


def add(buf, start, sig, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= buf.shape[0]:
        return
    sig = sig[: buf.shape[0] - i] * gain
    buf[i:i + len(sig), 0] += sig * (1 - pan) / 1.0 if pan > 0 else sig
    buf[i:i + len(sig), 1] += sig * (1 + pan) / 1.0 if pan < 0 else sig


def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    freq = 50 + 70 * np.exp(-t * 28)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    return np.sin(phase) * np.exp(-t * 9)


def hat(rng):
    n = int(0.06 * SR)
    noise = rng.standard_normal(n)
    noise = np.diff(np.concatenate([[0], noise]))  # crude high-pass
    return noise * np.exp(-np.arange(n) / SR * 70)


def clap(rng):
    n = int(0.18 * SR)
    noise = rng.standard_normal(n)
    return noise * np.exp(-np.arange(n) / SR * 22) * 0.6


def render(segments=SEGMENTS, length=LENGTH):
    rng = np.random.default_rng(7)
    buf = np.zeros((int(length * SR), 2))
    k, h, c = kick(), hat(rng), clap(rng)
    for i, (start, chord, drums, arp) in enumerate(segments):
        end = segments[i + 1][0] if i + 1 < len(segments) else length
        dur = end - start
        notes, bass = CHORDS[chord]
        # warm pad with a soft crossfade into the next chord
        for j, m in enumerate(notes):
            sig = tone(hz(m), dur + 0.5, harmonics=7, rolloff=1.7, detune=(j - 1.5) * 0.0015)
            sig *= env_adsr(len(sig), 0.35, 0.5)
            add(buf, start, sig, 0.055, pan=(j - 1.5) * 0.25)
        beats = np.arange(start, end - 0.01, BEAT)
        for b_i, b in enumerate(beats):
            # bass on every beat, a little longer on the downbeat
            note_len = BEAT * (0.95 if b_i % 4 == 0 else 0.6)
            sig = tone(hz(bass), note_len, harmonics=4, rolloff=1.2) * pluck_env(int(note_len * SR), 0.35)
            add(buf, b, sig, 0.16 if drums else 0.09)
            if drums:
                if b_i % 2 == 0:
                    add(buf, b, k, 0.55)
                else:
                    add(buf, b, c, 0.12)
                add(buf, b + BEAT / 2, h, 0.10, pan=0.3)
                add(buf, b, h, 0.05, pan=-0.3)
        if arp:
            pattern = [notes[1] + 12, notes[2] + 12, notes[3] + 12, notes[2] + 12]
            for n_i, t in enumerate(np.arange(start, end - 0.05, BEAT / 2)):
                m = pattern[n_i % 4]
                sig = tone(hz(m), 0.5, harmonics=5, rolloff=1.3) * pluck_env(int(0.5 * SR), 0.18)
                add(buf, t, sig, 0.07, pan=0.35 if n_i % 2 else -0.35)
    # final chord rings out; gentle fades at both ends; soft saturation as a limiter
    n = buf.shape[0]
    fade_in, fade_out = int(0.6 * SR), int(2.2 * SR)
    buf[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    buf[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]
    buf = np.tanh(buf * 1.4)
    buf *= 0.89 / np.max(np.abs(buf))
    return buf


def write_wav(path, buf):
    data = (buf * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "kf-music.wav"
    if "--timeline" in sys.argv:
        tl = json.loads(Path(sys.argv[sys.argv.index("--timeline") + 1]).read_text())
        write_wav(out, render(segments_from_timeline(tl["starts"], tl["duration"]), tl["duration"]))
    else:
        write_wav(out, render())
    print("wrote", out)
