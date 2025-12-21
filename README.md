# Melody Engine

![Lint](https://github.com/zbhavyai/melody-engine/actions/workflows/lint.yml/badge.svg)
![Release](https://github.com/zbhavyai/melody-engine/actions/workflows/release.yml/badge.svg)

Prompt based instrumental music generation.

## :sparkles: Features

Melody Engine is a thin but practical wrapper on [MagentaRT](https://github.com/magenta/magenta-realtime), providing:

1. REST API for programmatic music generation
1. Serialized job queue to avoid GPU thrashing
1. Containerized runtime for reproducible deployment
1. Simple interface that hides MagentaRT’s operational complexity

## :toolbox: Requirements

You would need a machine with a powerful Nvidia GPU, and a linux host with `podman` or `docker` installed. The MagentaRT's official repository suggests a GPU with 40GB VRAM, but in my experience, a powerful enough GPU like NVIDIA RTX A5000 with 24GB VRAM works just fine.

## :rocket: Getting started

Build and run Melody Engine locally inside a container.

1. Build the container image.

   ```shell
   make container-build
   ```

1. Run the container. This will load MagentaRT on your GPU and start a `uvicorn` server on port `8080`.

   ```shell
   make container-run
   ```

1. Access the API documentation at [localhost/docs](http://127.0.0.1/docs) to explore the available endpoints.

1. Generated audio files are saved locally in the [`outputs`](./outputs) directory.

## :headphones: Example

Generate a 1-hour spacey electronica track using the REST API.

1. Submit a generation job. The response will include a job ID, which uniquely identifies your generation request.

   ```shell
   curl \
   --request POST \
   --location 'localhost:8080/api/v1/jobs' \
   --header 'Content-Type: application/json' \
   --data '{
      "prompt": "spacey electronica with drifting pads and gentle rhythmic motion",
      "duration_s": 3600,
      "gain_db": 0,
      "format": "mp3"
   }'
   ```

1. Poll the status of your job.

   ```shell
   curl --request GET --location 'localhost:8080/api/v1/jobs/{job_id}'
   ```

1. Once the job is complete, you may download the generated audio file.

   ```shell
   curl --request GET --location 'localhost:8080/api/v1/jobs/{job_id}/download' --output output.mp3
   ```
