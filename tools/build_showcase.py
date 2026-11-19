"""Build the narrated showcase video: voice-over, scenes timed to the voice, music ducked under it.

usage (Windows, in an environment with imageio-ffmpeg, pillow and numpy):
    python tools/build_showcase.py static static/assets/video

Uses the Windows text-to-speech voice set in VOICE. Edit NARRATION to change what is said;
one line per scene, in the same order as the video.
"""
import json
import math
import subprocess
import sys
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np

HERE = Path(__file__).parent
STATIC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
WORK = OUT / "_build"
VOICE, RATE = "Microsoft Zira Desktop", -1  # rate: -10 (slow) to 10 (fast)

# One line per scene: intro, 5 cleaning scenes, real estate card, 4 real estate scenes, outro.
# "Four Fortken" is how the voice should say "4Fortken"; change the spelling if it is pronounced differently.
NARRATION = [
    "Welcome to K F Four Fortken Holdings. Cleaner, safer, better kept properties.",
    "We provide professional cleaning for offices, homes, institutions and commercial premises.",
    "After building or renovation, our post-construction cleaning leaves your space spotless and ready to use.",
    "Our fumigation and pest control services are safe and effective.",
    "We offer scheduled garbage collection and sustainable waste management.",
    "And we design and care for gardens, lawns and outdoor spaces.",
    "We also offer real estate services.",
    "We manage residential and commercial properties, including Hibiscus Homes in Shanzu.",
    "Our facilities management keeps buildings safe and running smoothly.",
    "We collect rent on time, with clear statements for landlords.",
    "And we help you buy, sell and value land and property.",
    "Call or WhatsApp us today, or send an enquiry on our website. K F Four Fortken Holdings. Your trusted property partner.",
]
FADE, BAR = 0.6, 1.3       # video crossfade; music half-bar (2 beats at 92 bpm)
LEAD, TAIL = 0.4, 0.5      # silence before and after each line within its scene
MIN_SCENE = 2.6


def speak(lines, folder):
    """Render each line to a WAV with Windows' built-in speech (System.Speech)."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "lines.json").write_text(json.dumps(lines), encoding="utf-8")
    ps = f"""
Add-Type -AssemblyName System.Speech
$lines = Get-Content -Raw -Encoding UTF8 '{folder / "lines.json"}' | ConvertFrom-Json
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(22050, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
for ($i = 0; $i -lt $lines.Count; $i++) {{
  $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
  $s.SelectVoice('{VOICE}'); $s.Rate = {RATE}; $s.Volume = 100
  $s.SetOutputToWaveFile((Join-Path '{folder}' ('line{{0:D2}}.wav' -f $i)), $fmt)
  $s.Speak($lines[$i]); $s.Dispose()
}}
"""
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    return [folder / f"line{i:02d}.wav" for i in range(len(lines))]


def read_wav(path):
    with wave.open(str(path)) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        data = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768
    return (data.reshape(-1, ch) if ch > 1 else data[:, None]), sr


def trim(sig, threshold=0.01):
    loud = np.nonzero(np.abs(sig).max(axis=1) > threshold)[0]
    return sig[loud[0]:loud[-1] + 1] if len(loud) else sig


def scene_lengths(durations):
    """Each scene lasts long enough for its line, rounded to whole half-bars so the beat stays steady."""
    lengths = []
    for i, d in enumerate(durations):
        visible = max(MIN_SCENE if 0 < i < len(durations) - 1 else 0, LEAD + d + TAIL)
        if i == len(durations) - 1:
            lengths.append(round(visible + 1.8, 2))  # outro: let the contacts linger
        else:
            lengths.append(round(math.ceil(visible / BAR) * BAR + FADE, 2))
    return lengths


def mix(voice_lines, starts, duration, music_path, out_path):
    music, sr = read_wav(music_path)
    voice = np.zeros(len(music), np.float32)
    for i, (sig, vsr) in enumerate(voice_lines):
        mono = trim(sig)[:, 0]
        x = np.interp(np.arange(0, len(mono), vsr / sr), np.arange(len(mono)), mono)  # resample to 44.1 kHz
        at = int((starts[i] + (0.6 if i == 0 else LEAD)) * sr)
        voice[at:at + len(x)] += x[: len(voice) - at]
    voice *= 0.92 / max(1e-6, np.abs(voice).max())
    # duck the music while the voice speaks (smoothed envelope)
    active = (np.abs(voice) > 0.02).astype(np.float32)
    k = int(0.35 * sr)
    csum = np.concatenate([[0.0], np.cumsum(active, dtype=np.float64)])  # moving average via running sums
    lo = np.clip(np.arange(len(active)) - k // 2, 0, len(active))
    hi = np.clip(np.arange(len(active)) + k // 2, 0, len(active))
    env = ((csum[hi] - csum[lo]) / k).astype(np.float32)
    env = np.clip(env * 4, 0, 1)
    music_gain = 0.85 - 0.62 * env
    out = music * music_gain[:, None] * 0.8 + voice[:, None]
    out = np.tanh(out * 1.1)
    out *= 0.89 / np.abs(out).max()
    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((out * 32767).astype("<i2").tobytes())


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    paths = speak(NARRATION, WORK / "voice")
    lines = [read_wav(p) for p in paths]
    durations = [len(trim(sig)) / sr for sig, sr in lines]
    timeline = {"lengths": scene_lengths(durations), "narration": NARRATION, "speech_seconds": durations}
    tl_path = WORK / "timeline.json"
    tl_path.write_text(json.dumps(timeline, indent=1))
    py = sys.executable
    subprocess.run([py, str(HERE / "make_video.py"), str(STATIC), str(WORK), "--timeline", str(tl_path)], check=True)
    timeline = json.loads(tl_path.read_text())
    subprocess.run([py, str(HERE / "make_music.py"), str(WORK / "music.wav"), "--timeline", str(tl_path)], check=True)
    mix(lines, timeline["starts"], timeline["duration"], WORK / "music.wav", WORK / "soundtrack.wav")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ffmpeg, "-loglevel", "error", "-y", "-i", str(WORK / "kf-services.mp4"), "-i", str(WORK / "soundtrack.wav"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
                    "-movflags", "+faststart", str(OUT / "kf-services.mp4")], check=True)
    (WORK / "kf-services-poster.jpg").replace(OUT / "kf-services-poster.jpg")
    print(f"done: {OUT / 'kf-services.mp4'} ({timeline['duration']:.1f}s)")


if __name__ == "__main__":
    main()
