# Melody Engine

![Lint](https://github.com/zbhavyai/melody-engine/actions/workflows/lint.yml/badge.svg)
![Release](https://github.com/zbhavyai/melody-engine/actions/workflows/release.yml/badge.svg)

Prompt based instrumental music generation for any given duration.

## :rocket: Getting started

Build from source and run it locally.

1. Initialize the project

   ```shell
   make init
   ```

1. Run the interactive CLI

   ```shell
   make run
   ```

1. Fill in the prompts, example

   ```shell
   Enter music prompt [peaceful ambient pads]: Soft acoustic guitar instrumental with warm, emotional tone
   Enter duration (seconds) [60.0]: 3600
   Enter output file name [music.mp3]: guitar.mp3
   Enter gain (dB) [0.0]: 0
   ```

1. Your generated audio file will appear in [`outputs`](./outputs) directory.

## :package: Installation

You can also build the wheel package, install it, and run the CLI without the source tree.

1. Build the wheel package

   ```shell
   make build
   ```

1. Install it into any Python environment

   ```shell
   <activate your virtual environment>
   pip install dist/melody_engine-*.whl
   ```

1. Run the interactive CLI from anywhere

   ```shell
   melody-engine
   ```
