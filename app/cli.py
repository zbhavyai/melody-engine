from __future__ import annotations

from pathlib import Path

import click

from app.generator import generate_music

VALID_FORMATS = {"wav", "flac", "mp3"}


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
    "out_name",
    type=str,
    help="Output file name",
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
    out_name: str | None,
    gain_db: float | None,
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

    if out_name is None:
        out_name = click.prompt(
            "Enter output file name",
            default="music.mp3",
            type=str,
        )

    if gain_db is None:
        gain_db = click.prompt(
            "Enter gain (dB)",
            default=0.0,
            type=float,
        )

    # type checkers should now know all are concrete types
    assert isinstance(prompt, str)
    assert isinstance(duration_s, float)
    assert isinstance(out_name, str)
    assert isinstance(gain_db, float)

    if duration_s <= 0:
        raise click.BadParameter("Duration must be greater than zero.")

    path = Path(out_name)
    ext = path.suffix.lower().lstrip(".")

    if ext not in VALID_FORMATS:
        fmt = "mp3"
        path = path.with_suffix(".mp3")
    else:
        fmt = ext

    if not path.suffix:
        path = path.with_suffix(f".{fmt}")

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    out_path = output_dir / path.name

    duration_ms = int(round(duration_s * 1000))
    generate_music(prompt, duration_ms, str(out_path), fmt, gain_db)


if __name__ == "__main__":
    main()
