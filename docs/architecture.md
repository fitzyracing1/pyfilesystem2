# Architecture

| Path | Role |
|---|---|
| `fs/base.py` | `FS` abstract base class |
| `fs/osfs.py, memoryfs.py, tempfs.py, zipfs.py, tarfs.py, ftpfs.py, mountfs.py, multifs.py, subfs.py` | filesystem implementations |
| `fs/opener/` | URL openers (`open_fs`) |
| `fs/copy.py, move.py, mirror.py, walk.py, glob.py` | utilities |
| `docs/source/` | Sphinx documentation (upstream) |
| `tests/` | pytest/unittest suite |

The Markdown pages in `docs/` sit next to the existing Sphinx sources and do not change them.
