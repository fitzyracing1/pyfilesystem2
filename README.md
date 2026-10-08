# fitzyracing-fs (PyFilesystem2)

> Part of **[360 Bench](https://github.com/fitzyracing1/360-bench)**, tested fixes for abandoned PyPI packages.

Python's Filesystem abstraction layer.

[![PyPI](https://img.shields.io/pypi/v/fitzyracing-fs.svg)](https://pypi.org/project/fitzyracing-fs/)

> **This is a fork of [fs / PyFilesystem2](https://github.com/PyFilesystem/pyfilesystem2)
> by [Will McGugan](https://github.com/willmcgugan), [Martin Larralde](https://github.com/althonos)
> and the PyFilesystem2 contributors**, published as a drop-in replacement that can be imported
> again. The upstream package has not been released since 2.4.16 (May 2022). Since setuptools 82
> (February 2026) removed `pkg_resources`, a fresh `pip install fs` can no longer be imported, and
> the pull requests that fix it have not been merged. The import name is still `fs`, so no code
> changes are needed. All credit for the original library goes to its authors and contributors;
> it remains available under the same MIT license.


## What's fixed in this fork

Based on upstream `fs==2.4.16` (tag [`v2.4.16`](https://github.com/PyFilesystem/pyfilesystem2/tree/v2.4.16));
the API and behaviour are unchanged.

- **`import fs` works again without `pkg_resources`.** `fs` depended on an unpinned `setuptools`
  and called `pkg_resources` at import time, so with setuptools 82+ every fresh install failed with
  `ModuleNotFoundError: No module named 'pkg_resources'`, on every Python version (older setuptools
  versions printed a `UserWarning: pkg_resources is deprecated as an API` instead). This fork:
  - declares `fs` and `fs.opener` as namespace packages with the standard library's
    `pkgutil.extend_path` instead of `pkg_resources.declare_namespace`, so extensions that add
    modules under `fs.*` / `fs.opener.*` (fs.sshfs, fs.smbfs, fs.dropboxfs, ...) are still
    found, even when they are installed in a different `sys.path` entry. (One edge case: a
    development checkout of an old extension that ships its own `pkg_resources`-style
    `fs/__init__.py` must not come *before* the fork on `sys.path`, or that file runs instead
    of the fork's. Wheels of the extensions listed above don't ship such a file.);
  - discovers opener plugins registered under the `fs.opener` entry point group (fs-s3fs,
    fs.sshfs, ...) with `importlib.metadata` instead of `pkg_resources.iter_entry_points`. It
    keeps the same semantics: plugins appear in `registry.protocols`, the first matching entry
    point wins, and the same `EntryPointError` messages are raised for broken plugins;
  - no longer depends on `setuptools` at all.

  Upstream issues: [#577](https://github.com/PyFilesystem/pyfilesystem2/issues/577),
  [#597](https://github.com/PyFilesystem/pyfilesystem2/issues/597);
  unmerged PRs: [#589](https://github.com/PyFilesystem/pyfilesystem2/pull/589),
  [#590](https://github.com/PyFilesystem/pyfilesystem2/pull/590), both by
  [@eli-schwartz](https://github.com/eli-schwartz). The namespace change is #590 as proposed.
  The entry-point change follows #589 with one correction: on Python 3.10+, #589 as written
  calls `entry_points(group=..., name=None)`, which matches no entry points. As a result
  `registry.protocols` silently lost every plugin protocol (opening a plugin URL still worked).
  The fork's tests cover that case with a dummy plugin.
- **`geturl(..., purpose="fs")` works on Python 3.14** (2.4.18). Python 3.14's
  `urllib.request.pathname2url()` returns `///tmp/x` for `/tmp/x`, so `OSFS.geturl()` returned
  `osfs://///tmp/x` instead of `osfs:///tmp/x` (same for `zip://` and `tar://` URLs from `ZipFS`
  and `TarFS`). The URLs are now the same as on Python 3.9 to 3.13, and 3.14 is tested in CI.
- **Packaging:** `pyproject.toml` replaces `setup.py`; Python 3.9+ (Python 2.7 and 3.5 to 3.8 are no
  longer supported. If you are stuck on those, keep upstream `fs==2.4.16` with `setuptools<82`).

Not included: the changes on upstream `master` that were merged after 2.4.16 but never released
(new `Walker` glob filters, a reworked copy/move that raises new errors). They change behaviour,
so they don't belong in a patch release that is meant to be a drop-in replacement.


## Install

```bash
pip install fitzyracing-fs
```

### Switching from `fs`

This distribution installs the same `fs` import package as the original, so your code keeps
doing `import fs` / `from fs import open_fs`. **Uninstall the original first**, then install the
fork:

```bash
pip uninstall -y fs
pip install fitzyracing-fs
```

The order matters. Both distributions own the same files, so if you install the fork first and
uninstall `fs` afterwards, pip deletes the shared `fs/` files and the import breaks. If that
happens, run `pip install --force-reinstall --no-deps fitzyracing-fs`.

In `requirements.txt` / `pyproject.toml`, replace `fs` with `fitzyracing-fs`.

### If you get fs through another package

pip has no equivalent of npm's `overrides`: it cannot replace a dependency with a differently
named package. If one of your dependencies requires `fs` (fs-s3fs, fs.sshfs and others do), pip
will keep installing the original. So you install the fork alongside it, and since both provide
the same `fs` import name you then have to remove the original:

```bash
pip install fitzyracing-fs
pip uninstall -y fs
pip install --force-reinstall --no-deps fitzyracing-fs   # restore the files the uninstall removed
```

Afterwards `pip check` reports `<package> requires fs, which is not installed`; that is expected.
Any later `pip install`/`--upgrade` that pulls `fs` back in will overwrite the fork's files, so
repeat the steps above after upgrading the package that depends on it. If you can't switch, the
other workaround is to pin `setuptools<82` in that environment.

**uv users** can do this properly with an override that drops the original:

```toml
# pyproject.toml
[project]
dependencies = ["fitzyracing-fs", "...the package that depends on fs..."]

[tool.uv]
override-dependencies = ["fs; sys_platform == 'never'"]
```

(or `uv pip install --override overrides.txt ...` with that same line in `overrides.txt`).

### Extensions that use `pkg_resources` themselves

Some extensions call `pkg_resources` in their own code. fs.sshfs 1.0.2 and fs.smbfs 1.0.7, for
example, read their version with `pkg_resources.resource_string`. They fail to import without
setuptools < 82 no matter which `fs` you use. With this fork, `open_fs("ssh://...")` then raises a
clear `EntryPointError: could not load entry point; No module named 'pkg_resources'`. Extensions
that don't use it, such as fs-s3fs, work as before.


## Documentation

- [Wiki](https://www.pyfilesystem.org)
- [API Documentation](https://docs.pyfilesystem.org/)
- [GitHub Repository](https://github.com/PyFilesystem/pyfilesystem2)
- [Blog](https://www.willmcgugan.com/tag/fs/)

## Introduction

Think of PyFilesystem's `FS` objects as the next logical step to
Python's `file` objects. In the same way that file objects abstract a
single file, FS objects abstract an entire filesystem.

Let's look at a simple piece of code as an example. The following
function uses the PyFilesystem API to count the number of non-blank
lines of Python code in a directory. It works _recursively_, so it will
find `.py` files in all sub-directories.

```python
def count_python_loc(fs):
    """Count non-blank lines of Python code."""
    count = 0
    for path in fs.walk.files(filter=['*.py']):
        with fs.open(path) as python_file:
            count += sum(1 for line in python_file if line.strip())
    return count
```

We can call `count_python_loc` as follows:

```python
from fs import open_fs
projects_fs = open_fs('~/projects')
print(count_python_loc(projects_fs))
```

The line `project_fs = open_fs('~/projects')` opens an FS object that
maps to the `projects` directory in your home folder. That object is
used by `count_python_loc` when counting lines of code.

To count the lines of Python code in a _zip file_, we can make the
following change:

```python
projects_fs = open_fs('zip://projects.zip')
```

Or to count the Python lines on an FTP server:

```python
projects_fs = open_fs('ftp://ftp.example.org/projects')
```

No changes to `count_python_loc` are necessary, because PyFileystem
provides a simple consistent interface to anything that resembles a
collection of files and directories. Essentially, it allows you to write
code that is independent of where and how the files are physically
stored.

Contrast that with a version that purely uses the standard library:

```python
def count_py_loc(path):
    count = 0
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.endswith('.py'):
                with open(os.path.join(root, name), 'rt') as python_file:
                    count += sum(1 for line in python_file if line.strip())
    return count
```

This version is similar to the PyFilesystem code above, but would only
work with the OS filesystem. Any other filesystem would require an
entirely different API, and you would likely have to re-implement the
directory walking functionality of `os.walk`.

## Credits

This fork contains no new functionality; it exists only to keep PyFilesystem2 installable.
The `pkg_resources` replacement is based on [@eli-schwartz](https://github.com/eli-schwartz)'s
upstream PRs [#589](https://github.com/PyFilesystem/pyfilesystem2/pull/589) and
[#590](https://github.com/PyFilesystem/pyfilesystem2/pull/590). Fork maintained by
[Joshua Almeida](https://github.com/fitzyracing1).

The following developers have contributed code and their time to this projects:

- [Will McGugan](https://github.com/willmcgugan)
- [Martin Larralde](https://github.com/althonos)
- [Giampaolo Cimino](https://github.com/gpcimino)
- [Geoff Jukes](https://github.com/geoffjukes)

See [CONTRIBUTORS.md](https://github.com/PyFilesystem/pyfilesystem2/blob/master/CONTRIBUTORS.md)
for a full list of contributors.

PyFilesystem2 owes a massive debt of gratitude to the following
developers who contributed code and ideas to the original version.

- Ryan Kelly
- Andrew Scheller
- Ben Timby

Apologies if I missed anyone, feel free to prompt me if your name is
missing here.

## Support

Problems specific to this fork (installation, `pkg_resources`): please use the
[fork's issue tracker](https://github.com/fitzyracing1/pyfilesystem2/issues).

If commercial support is required, please contact [Will McGugan](mailto:willmcgugan@gmail.com)
(this refers to the original project, not to the fork).

## Security contact

To report a security vulnerability in this fork, please use
[GitHub private vulnerability reporting](https://github.com/fitzyracing1/pyfilesystem2/security/advisories/new)
rather than a public issue.

## License

[MIT](./LICENSE) - Copyright (c) 2017-2021 The PyFilesystem2 contributors, Copyright (c) 2016-2019
Will McGugan. The original license and copyright notice are retained unchanged; fork changes are
released under the same license.

Original project: https://github.com/PyFilesystem/pyfilesystem2
