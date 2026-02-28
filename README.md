# Piper Recording Studio

## Overview

**Note: This is a draft summary for review and can be refined based on feedback.**

Piper Recording Studio is a web-based tool designed to help users create custom text-to-speech (TTS) voice datasets for training [Piper TTS models](https://github.com/rhasspy/piper). It provides a user-friendly interface for recording audio prompts in multiple languages, making the voice dataset creation process accessible to both individual contributors and teams.

### Key Features

- **Browser-based Recording Interface**: Simple web UI accessible at localhost:8000 for recording voice prompts
- **Multi-language Support**: Pre-configured prompts for various languages stored in the `prompts/` directory
- **Dataset Export**: Built-in tools to export recordings in Piper-compatible LJSpeech format
- **Docker Support**: Easy deployment with Docker for cross-platform compatibility
- **Multi-user Mode**: Collaborative recording with login codes for team-based dataset creation
- **Flexible Deployment**: Can run with or without Docker

### Getting Started

The easiest way to get started is using Docker:

```sh
docker run -it -p 8000:8000 -v '/path/to/output:/app/output' rhasspy/piper-recording-studio
```

Then visit http://localhost:8000 to select a language and begin recording. For more detailed instructions, see the sections below.

---

## Detailed Documentation

Local tool for recording yourself to train a [Piper text to speech](https://github.com/rhasspy/piper) voice.

![Screen shot](etc/screenshot.jpg)

[![Sponsored by Nabu Casa](etc/nabu_casa_sponsored.png)](https://nabucasa.com)

## Tutorial

See a [video tutorial](https://www.youtube.com/watch?v=Z1pptxLT_3I) by [Thorsten Müller](https://www.thorsten-voice.de/)

## Docker

```sh
docker run -it -p 8000:8000 -v '/path/to/output:/app/output' rhasspy/piper-recording-studio
```

Visit http://localhost:8000 to select a language and start recording.

Add `--help` to see more options.

### Building

```sh
docker build . -t rhasspy/piper-recording-studio
```

## Installing without Docker

```sh
git clone https://github.com/rhasspy/piper-recording-studio.git
cd piper-recording-studio/

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## Running without Docker

```sh
python3 -m piper_recording_studio
```

Visit http://localhost:8000 to select a language and start recording.

Prompts are in the `prompts/` directory with the following format:

* Language directories are named `<language name>_<language code>`
* Each `.txt` in a language directory contains lines with:
  * `<id>\t<text>` or
  * `text` (id is automatically assigned based on line number)

Output audio is written to `output/`

See `--debug` for more options.

## Exporting

Install ffmpeg:

```sh
sudo apt-get install ffmpeg
```

Install exporting dependencies:

```sh
python3 -m pip install -r requirements_export.txt
```

Export recordings for a language to a Piper-compatible dataset (LJSpeech format):

```sh
python3 -m export_dataset output/<language>/ /path/to/dataset
```

Requires a non-Docker install. If you used Docker to record your dataset, you may need to adjust the permissions of the output directory:

```sh
sudo chown -R "$(id -u):$(id -u)" output/
```

See `--help` for more options. You may need to adjust the silence detection parameters to correctly remove button clicks and keypresses.

## Multi-User Mode

```sh
python3 -m piper_recording_studio --multi-user
```

Now a "login code" will be required to record. A directory `output/user_<code>/` must exist for each user and language.
