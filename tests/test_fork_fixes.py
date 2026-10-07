# coding: utf-8
"""Regression tests for the fitzyracing-fs fork (360 Bench).

Upstream issues #577 / #597: with setuptools >= 82 (no ``pkg_resources``) a fresh
``pip install fs`` cannot be imported, because ``fs`` and ``fs.opener`` declared
themselves as namespace packages with ``pkg_resources.declare_namespace`` and the
opener registry loaded plugins with ``pkg_resources.iter_entry_points``.

Every check runs in a subprocess where ``import pkg_resources`` fails, i.e. the
situation on a fresh install with setuptools 82+.
"""

from __future__ import unicode_literals

import io
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _fs_home():
    # Directory that contains the `fs` package under test: the source tree,
    # or site-packages when the suite is run against an installed wheel.
    import fs

    return os.path.dirname(os.path.dirname(os.path.abspath(fs.__file__)))

BLOCK_PKG_RESOURCES = "import sys; sys.modules['pkg_resources'] = None\n"


def _write(path, text):
    d = os.path.dirname(path)
    if not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(text))


class _SubprocessTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fs-fork-test-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_code(self, code, extra_path=()):
        # The `fs` under test comes first, extra entries (plugin
        # "site-packages" directories) after it, like separate install
        # locations on sys.path.
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([_fs_home()] + list(extra_path))
        env.pop("PYTHONSTARTUP", None)
        proc = subprocess.run(
            [sys.executable, "-c", BLOCK_PKG_RESOURCES + textwrap.dedent(code)],
            cwd=self.tmp,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout)
        return proc.stdout


class TestImportWithoutPkgResources(_SubprocessTest):
    def test_import_and_open_builtin_filesystems(self):
        out = self.run_code(
            """
            import fs, fs.opener
            from fs import open_fs
            with open_fs("mem://") as m:
                m.writetext("a.txt", "hello")
                print(m.readtext("a.txt"))
            with open_fs("temp://") as t:
                print(type(t).__name__)
            print(sorted(p for p in fs.opener.registry.protocols if p in ("mem", "osfs", "zip", "tar", "ftp", "temp")))
            """
        )
        self.assertIn("hello", out)
        self.assertIn("TempFS", out)
        self.assertIn("['ftp', 'mem', 'osfs', 'tar', 'temp', 'zip']", out)

    def test_no_pkg_resources_in_package_sources(self):
        # Look at the code (imports, __import__ calls, names), not comments.
        import ast

        offenders = []
        for dirpath, _, filenames in os.walk(os.path.join(ROOT, "fs")):
            for name in filenames:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(dirpath, name)
                with io.open(path, encoding="utf-8") as f:
                    tree = ast.parse(f.read(), path)
                for node in ast.walk(tree):
                    hit = (
                        isinstance(node, ast.Import)
                        and any(a.name.split(".")[0] == "pkg_resources" for a in node.names)
                    ) or (
                        isinstance(node, ast.ImportFrom)
                        and (node.module or "").split(".")[0] == "pkg_resources"
                    ) or (
                        isinstance(node, ast.Name) and node.id == "pkg_resources"
                    ) or (
                        isinstance(node, ast.Call)
                        and getattr(node.func, "id", None) == "__import__"
                        and node.args
                        and getattr(node.args[0], "value", None) == "pkg_resources"
                    )
                    if hit:
                        offenders.append("%s:%d" % (os.path.relpath(path, ROOT), node.lineno))
        self.assertEqual(offenders, [])


class TestNamespacePackages(_SubprocessTest):
    """Third-party extensions add modules under ``fs.*`` and ``fs.opener.*``
    (e.g. fs.sshfs ships ``fs/sshfs/`` and ``fs/opener/sshfs.py``). They must
    still be importable when they live in a different sys.path entry."""

    def test_pkg_resources_style_portion_in_another_sys_path_entry(self):
        # The layout upstream supported: the extension's directory carries its
        # own pkg_resources-style fs/__init__.py and fs/opener/__init__.py.
        # Those files are not executed (they are not first on sys.path), but
        # the modules beside them must be importable.
        legacy = os.path.join(self.tmp, "legacy-site")
        ns_init = "__import__('pkg_resources').declare_namespace(__name__)\n"
        _write(os.path.join(legacy, "fs", "__init__.py"), ns_init)
        _write(os.path.join(legacy, "fs", "opener", "__init__.py"), ns_init)
        _write(os.path.join(legacy, "fs", "legacyfs", "__init__.py"), "NAME = 'legacyfs'\n")
        _write(os.path.join(legacy, "fs", "opener", "legacy_opener.py"), "NAME = 'legacy_opener'\n")
        out = self.run_code(
            """
            import fs.legacyfs, fs.opener.legacy_opener
            print(fs.legacyfs.NAME, fs.opener.legacy_opener.NAME)
            import fs.osfs  # the fork's own modules still resolve
            print(fs.osfs.OSFS.__module__, fs.opener.registry.__class__.__name__)
            """,
            extra_path=[legacy],
        )
        self.assertIn("legacyfs legacy_opener", out)
        self.assertIn("fs.osfs Registry", out)

    def test_pep420_style_portion_in_another_sys_path_entry(self):
        # A portion without any fs/__init__.py (how pip lays out wheels of
        # extensions such as fs.sshfs). Upstream's pkg_resources namespace did
        # not find these in a separate sys.path entry; pkgutil.extend_path does.
        site = os.path.join(self.tmp, "plugin-site")
        _write(os.path.join(site, "fs", "probefs", "__init__.py"), "NAME = 'probefs'\n")
        _write(os.path.join(site, "fs", "opener", "probe_opener.py"), "NAME = 'probe_opener'\n")
        out = self.run_code(
            """
            import fs.probefs, fs.opener.probe_opener
            print(fs.probefs.NAME, fs.opener.probe_opener.NAME)
            """,
            extra_path=[site],
        )
        self.assertIn("probefs probe_opener", out)


class TestEntryPointOpeners(_SubprocessTest):
    """Openers registered through the ``fs.opener`` entry point group (how
    fs-s3fs, fs.sshfs, fs.dropboxfs, ... plug in) must keep working."""

    def make_dummy_distribution(self, entry_points):
        site = os.path.join(self.tmp, "dummy-site")
        _write(
            os.path.join(site, "dummy_fs_plugin.py"),
            """
            from fs.memoryfs import MemoryFS
            from fs.opener import Opener

            class DummyFS(MemoryFS):
                pass

            class DummyOpener(Opener):
                protocols = ["dummy"]

                def open_fs(self, fs_url, parse_result, writeable, create, cwd):
                    dfs = DummyFS()
                    dfs.writetext("resource.txt", parse_result.resource)
                    return dfs

            class NotAnOpener(object):
                pass
            """,
        )
        dist_info = os.path.join(site, "dummy_fs_plugin-1.0.dist-info")
        _write(
            os.path.join(dist_info, "METADATA"),
            "Metadata-Version: 2.1\nName: dummy-fs-plugin\nVersion: 1.0\n",
        )
        _write(os.path.join(dist_info, "entry_points.txt"), entry_points)
        return site

    def test_entry_point_opener_is_listed_and_opened(self):
        site = self.make_dummy_distribution(
            "[fs.opener]\n"
            "dummy = dummy_fs_plugin:DummyOpener\n"
            "dummy2 = dummy_fs_plugin:DummyOpener\n"
        )
        out = self.run_code(
            """
            from fs.opener import open_fs, registry
            protocols = registry.protocols
            print("dummy" in protocols, "dummy2" in protocols, protocols.count("dummy"))
            with open_fs("dummy://some/where") as d:
                print(type(d).__name__, d.readtext("resource.txt"))
            print(type(registry.get_opener("dummy2")).__name__)
            """,
            extra_path=[site],
        )
        self.assertIn("True True 1", out)
        self.assertIn("DummyFS some/where", out)
        self.assertIn("DummyOpener", out)

    def test_unknown_protocol_and_bad_entry_points(self):
        site = self.make_dummy_distribution(
            "[fs.opener]\n"
            "broken = dummy_fs_plugin:DoesNotExist\n"
            "notopener = dummy_fs_plugin:NotAnOpener\n"
        )
        out = self.run_code(
            """
            from fs.opener import open_fs
            from fs.opener.errors import EntryPointError, UnsupportedProtocol
            for url in ("nosuchproto://", "broken://", "notopener://"):
                try:
                    open_fs(url)
                except UnsupportedProtocol as e:
                    print("UnsupportedProtocol", e)
                except EntryPointError as e:
                    print("EntryPointError", e)
            """,
            extra_path=[site],
        )
        self.assertIn("UnsupportedProtocol protocol 'nosuchproto' is not supported", out)
        self.assertIn("EntryPointError could not load entry point;", out)
        self.assertIn("EntryPointError entry point did not return an opener", out)

    def test_load_extern_false_ignores_entry_points(self):
        site = self.make_dummy_distribution("[fs.opener]\ndummy = dummy_fs_plugin:DummyOpener\n")
        out = self.run_code(
            """
            from fs.opener.registry import Registry
            from fs.opener.errors import UnsupportedProtocol
            r = Registry(load_extern=False)
            print("dummy" in r.protocols)
            try:
                r.get_opener("dummy")
            except UnsupportedProtocol:
                print("unsupported")
            """,
            extra_path=[site],
        )
        self.assertIn("False", out)
        self.assertIn("unsupported", out)


if __name__ == "__main__":
    unittest.main()
