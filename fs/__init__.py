"""Python filesystem abstraction layer.
"""

# pkgutil-style namespace package: also look for ``fs`` modules in other
# sys.path entries (extensions such as fs.sshfs add ``fs.*`` modules).
# This used to be ``pkg_resources.declare_namespace``, which no longer exists
# with setuptools 82+.
__path__ = __import__("pkgutil").extend_path(__path__, __name__)  # type: ignore

from . import path
from ._fscompat import fsdecode, fsencode
from ._version import __version__
from .enums import ResourceType, Seek
from .opener import open_fs

__all__ = ["__version__", "ResourceType", "Seek", "open_fs"]
