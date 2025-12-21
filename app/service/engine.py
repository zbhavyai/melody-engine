from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any, cast

import numpy as np
import soundfile as sf
from pydub import AudioSegment

from app.core.settings import settings

try:
    from magenta_rt import audio, system
except ImportError:
    audio = None
    system = None

logger = logging.getLogger(__name__)


class AudioEngine:
    _instance: AudioEngine | None = None
    _model: Any = None

    def __new__(cls) -> AudioEngine:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_magenta_rt_in_memory(self) -> None:
        """
        Loads the MagentaRT model into memory.
        """

        if self._model is not None:
            return

        if system is None:
            logger.error("magenta_rt module not found.")
            return

        logger.info(
            "Loading MagentaRT with (tag=%s, device=%s, lazy=%s)",
            settings.magenta_tag,
            settings.magenta_device,
            settings.magenta_lazy,
        )
        self._model = system.MagentaRT(
            tag=settings.magenta_tag,
            device=settings.magenta_device,
            lazy=settings.magenta_lazy,
        )
        logger.info("MagentaRT loaded successfully.")

    def generate_music(
        self,
        prompt: str,
        duration_ms: int,
        out_path: str,
        fmt: str = "wav",
        gain_db: float = 0.0,
    ) -> Path:
        """
        Generates music using the loaded MagentaRT model.

        Args:
            prompt: The prompt to generate music from.
            duration_ms: The duration of the generated music in milliseconds.
            out_path: The path to save the generated music to.
            fmt: The format of the generated music ("wav", "flac", "mp3").
            gain_db: The gain of the generated music in decibels.

        Returns:
            The path to the generated music.
        """

        if self._model is None:
            logger.error("MagentaRT is not loaded.")
            raise RuntimeError("MagentaRT is not loaded.")

        if audio is None:
            logger.error("magenta_rt module is not found.")
            raise RuntimeError("magenta_rt module is not found.")

        out_p = Path(out_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        duration_s = duration_ms / 1000.0

        # 1. Embed Style
        prompts = [prompt]
        styles = np.array([self._model.embed_style(p) for p in prompts])
        weights = np.array([1.0], dtype=np.float32)
        weights /= weights.sum()
        style = (weights[:, np.newaxis] * styles).mean(axis=0)

        # 2. Generate
        chunks = []
        state = None
        num_chunks = int(np.ceil(duration_s / self._model.config.chunk_length))
        num_samples = round(duration_s * self._model.sample_rate)

        logger.info("Starting generation for '%s' (%s)s", prompt, duration_s)

        for _ in range(num_chunks):
            chunk, state = self._model.generate_chunk(state=state, style=style)
            chunks.append(chunk)

        # 3. Concatenate & Process
        generated_waveform = audio.concatenate(chunks)
        generated_waveform = generated_waveform[:num_samples]

        # 4. Post-process via temp file
        with tempfile.TemporaryDirectory() as td:
            raw_temp_path = Path(td) / "raw_generation.wav"
            generated_waveform.write(str(raw_temp_path))

            data, sr = sf.read(str(raw_temp_path), always_2d=True)
            data = self._apply_gain(data, gain_db)
            data = self._trim_to_exact(data, sr, duration_ms)

            if fmt == "wav":
                self._sf_write(out_p, data, sr, subtype="PCM_16")
            elif fmt == "flac":
                self._sf_write(out_p, data, sr, format="FLAC")
            elif fmt == "mp3":
                tmpwav = out_p.with_suffix(".tmp.wav")
                self._sf_write(tmpwav, data, sr, subtype="PCM_16")
                seg = cast(AudioSegment, AudioSegment.from_wav(tmpwav))
                seg.export(out_p, format="mp3")
                tmpwav.unlink()
            else:
                raise ValueError(f"Unsupported format: {fmt}")

        logger.info("Generation complete -> %s", out_p)
        return out_p

    @staticmethod
    def _apply_gain(
        samples: np.ndarray,
        gain_db: float,
    ) -> np.ndarray:
        """
        Applies gain to the audio.
        """

        if abs(gain_db) < 1e-6:
            return samples
        gain = 10 ** (gain_db / 20.0)
        return np.clip(samples * gain, -1.0, 1.0)

    @staticmethod
    def _trim_to_exact(
        samples: np.ndarray,
        sr: int,
        target_ms: int,
    ) -> np.ndarray:
        """
        Trims the audio to the exact duration.
        """

        exact_samples = int(round(target_ms * sr / 1000.0))
        if len(samples) < exact_samples:
            return samples
        return samples[:exact_samples]

    @staticmethod
    def _sf_write(
        path: Path,
        data: np.ndarray,
        sr: int,
        subtype: str | None = None,
        format: str | None = None,
    ) -> None:
        """
        Writes the audio to the file.
        """

        sf.write(path, data, sr, subtype=subtype, format=format)
