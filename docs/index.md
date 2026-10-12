# fitzyracing-fs

`fitzyracing-fs` is a drop-in fork of [PyFilesystem2 (fs)](https://github.com/PyFilesystem/pyfilesystem2) and part of [360 Bench](https://github.com/fitzyracing1/360-bench). It is based on upstream `fs==2.4.16`, and the API is unchanged. All credit for the original library goes to its authors and contributors.

## What the fork fixes (summary of [README.md](../README.md))

- `import fs` works without `pkg_resources` (setuptools 82+).
- `geturl(..., purpose="fs")` works on Python 3.14.
- Packaging moved to `pyproject.toml`. Requires Python 3.9+.

The full details and links to the upstream issues are in [README.md](../README.md).

Pages: [Getting started](getting-started.md) · [Architecture](architecture.md)

## CI

`.github/workflows/test.yml` runs the pytest suite, and `package.yml` builds and checks distributions on `v2.*` tags. A run is **lit** when it succeeds and **dark** otherwise.

## License

MIT. The original notice is kept: Copyright (c) 2017-2021 The PyFilesystem2 contributors; Copyright (c) 2016-2019 Will McGugan.
Modifications: Copyright (c) 2026 Joshua Almeida.
