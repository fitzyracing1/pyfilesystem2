# Getting started

## Install

```
pip uninstall -y fs && pip install fitzyracing-fs
```

The import name is still `fs`.

## Usage

`import fs; fs.open_fs('osfs://.')`, plus `MemoryFS`, `TempFS`, `ZipFS`, `TarFS`, `FTPFS`, `MountFS` and so on. The upstream Sphinx docs are in `docs/source/` (build with `docs/Makefile`).

## Develop and test

```
python -m pip install -r tests/requirements.txt pytest
python -m pytest tests
```
