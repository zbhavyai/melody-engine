from __future__ import annotations

from pathlib import Path

import click

from app.generator import generate_music


@click.command()
@click.option(
    "--prompt",
    "prompt",
    type=str,
    help="Text prompt describing the music style",
)
@click.option(
    "--duration",
    "duration_s",
    type=float,
    help="Length in seconds (must be > 0)",
)
@click.option(
    "--out",
    "out_path",
    type=str,
    help="Output file path",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["wav", "flac", "mp3"]),
    default=None,
    help="Output format (default inferred from file extension)",
)
@click.option(
    "--gain",
    "gain_db",
    type=float,
    help="Gain adjustment (dB)",
)
def main(
    prompt: str | None,
    duration_s: float | None,
    out_path: str | None,
    fmt: str | None,
    gain_db: float,
) -> None:
    if prompt is None:
        prompt = click.prompt(
            "Enter music prompt",
            default="peaceful ambient pads",
            type=str,
        )

    if duration_s is None:
        duration_s = click.prompt(
            "Enter duration (seconds)",
            default=60.0,
            type=float,
        )

    if out_path is None:
        out_path = click.prompt(
            "Enter output file path",
            default="outputs/music.wav",
            type=str,
        )

    if gain_db == 0.0:
        gain_db = click.prompt(
            "Enter gain (dB)",
            default=0.0,
            type=float,
        )

    # type checkers should now know all are concrete types
    assert isinstance(prompt, str)
    assert isinstance(duration_s, float)
    assert isinstance(out_path, str)
    assert isinstance(gain_db, float)

    if fmt is None:
        ext = Path(out_path).suffix.lower().lstrip(".")
        fmt = ext if ext in ("wav", "flac", "mp3") else "wav"

    if duration_s <= 0:
        raise click.BadParameter("Duration must be greater than zero.")

    duration_ms = int(round(duration_s * 1000))
    generate_music(prompt, duration_ms, out_path, fmt, gain_db)


if __name__ == "__main__":
    main()
