from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import cast

import numpy as np
import soundfile as sf
from pydub import AudioSegment


def generate_music(
    prompt: str,
    duration_ms: int,
    out_path: str,
    fmt: str = "wav",
    gain_db: float = 0.0,
) -> None:
    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # add a safe margin to avoid truncation
    safe_margin_s = 6.0
    request_s = (duration_ms / 1000.0) + safe_margin_s

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        raw_path = td_path / "raw.mp3"

        # prepare cache directory for magenta_rt
        cache_path = Path("~/.cache/magenta_rt").expanduser()
        cache_path.mkdir(parents=True, exist_ok=True)

        # build the container command
        cmd = _build_container_command(prompt, request_s, cache_path, td_path)

        # run container
        subprocess.run(cmd, check=True)

        # load the result
        try:
            data_t: tuple[np.ndarray, int] = cast(tuple[np.ndarray, int], sf.read(raw_path, always_2d=True))
            data, sr = data_t
        except Exception:
            seg = cast(AudioSegment, AudioSegment.from_mp3(raw_path))
            sr = int(seg.frame_rate)
            samples = np.array(seg.get_array_of_samples()).reshape((-1, seg.channels)) / (2**15)
            data = samples.astype(np.float32)

        # process audio
        data = _apply_gain(data, gain_db)
        data = _trim_to_exact(data, sr, duration_ms)

        # write output
        if fmt == "wav":
            _sf_write(out_p, data, sr, subtype="PCM_16")
        elif fmt == "flac":
            _sf_write(out_p, data, sr, format="FLAC")
        elif fmt == "mp3":
            tmpwav = out_p.with_suffix(".tmp.wav")
            _sf_write(tmpwav, data, sr, subtype="PCM_16")
            seg = cast(AudioSegment, AudioSegment.from_wav(tmpwav))
            seg.export(out_p, format="mp3")
            tmpwav.unlink()
        else:
            raise ValueError(f"Unsupported format: {fmt}")

        print(f"Generated file: {out_p}")


def _build_container_command(
    prompt: str,
    request_s: float,
    cache_path: Path,
    td_path: Path,
) -> list[str]:
    engine = _detect_container_engine()

    return [
        engine,
        "container",
        "run",
        "--rm",
        "--interactive",
        "--device",
        "nvidia.com/gpu=all",
        "--volume",
        f"{cache_path}:/magenta-realtime/cache:rw,Z",
        "--volume",
        f"{td_path}:/io:rw,Z",
        "us-docker.pkg.dev/brain-magenta/magenta-rt/magenta-rt:gpu",
        "python3.12",
        "-m",
        "magenta_rt.generate",
        f"--prompt={prompt}",
        "--output=/io/raw.mp3",
        f"--duration={int(request_s)}",
    ]


def _detect_container_engine() -> str:
    if shutil.which("podman"):
        return "podman"
    if shutil.which("docker"):
        return "docker"
    raise RuntimeError("No container engine found.")


def _apply_gain(samples: np.ndarray, gain_db: float) -> np.ndarray:
    if abs(gain_db) < 1e-6:
        return samples
    gain = 10 ** (gain_db / 20.0)
    return np.clip(samples * gain, -1.0, 1.0)


def _trim_to_exact(samples: np.ndarray, sr: int, target_ms: int) -> np.ndarray:
    exact_samples = int(round(target_ms * sr / 1000.0))
    return samples[:exact_samples]


def _sf_write(
    path: Path,
    data: np.ndarray,
    sr: int,
    subtype: str | None = None,
    format: str | None = None,
) -> None:
    sf.write(path, data, sr, subtype=subtype, format=format)
