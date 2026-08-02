# discord-stream-controller

A small, async Python library for managing authorized media sources, queues,
state, and events in Discord bot projects.

> **Scope:** This package is a stream controller. It does not implement Discord
> Go Live or Screen Share video transport, because the standard Discord Bot API
> does not expose that capability.

## Features

- Per-guild stream sessions
- Async queue operations
- Start, stop, skip, pause, and resume state
- Source validation hooks
- Event callbacks
- No Discord library dependency
- Ready for GitHub and PyPI packaging

## Install

```bash
pip install discord-stream-controller
```

For local development:

```bash
pip install -e ".[dev]"
```

## Quick example

```python
import asyncio
from discord_stream_controller import StreamController

async def main():
    controller = StreamController()

    await controller.add(123, "https://example.com/authorized-media.mp4")
    current = await controller.start(123)

    print(current.url if current else "Queue is empty")

asyncio.run(main())
```

## Publishing

Update `YOUR_NAME` and `YOUR_USERNAME` in `pyproject.toml`, then:

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

Upload to TestPyPI first:

```bash
python -m twine upload --repository testpypi dist/*
```

Then upload to PyPI:

```bash
python -m twine upload dist/*
```

Never commit PyPI tokens. Use GitHub Actions secrets for automated publishing.

## License

MIT
