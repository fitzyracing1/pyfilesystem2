# coding: utf-8
"""Test url tools. """
from __future__ import unicode_literals

import platform
import shutil
import six
import tempfile
import unittest

try:
    from unittest import mock
except ImportError:
    import mock

from fs._url_tools import url_quote
from fs.osfs import OSFS


class TestBase(unittest.TestCase):
    def test_quote(self):
        test_fixtures = [
            # test_snippet, expected
            ["foo/bar/egg/foofoo", "foo/bar/egg/foofoo"],
            ["foo/bar ha/barz", "foo/bar%20ha/barz"],
            ["example b.txt", "example%20b.txt"],
            ["exampleㄓ.txt", "example%E3%84%93.txt"],
        ]
        if platform.system() == "Windows":
            test_fixtures.extend(
                [
                    ["C:\\My Documents\\test.txt", "C:/My%20Documents/test.txt"],
                    ["C:/My Documents/test.txt", "C:/My%20Documents/test.txt"],
                    # on Windows '\' is regarded as path separator
                    ["test/forward\\slash", "test/forward/slash"],
                ]
            )
        else:
            test_fixtures.extend(
                [
                    # colon:tmp is bad path under Windows
                    ["test/colon:tmp", "test/colon%3Atmp"],
                    # Unix treat \ as %5C
                    ["test/forward\\slash", "test/forward%5Cslash"],
                ]
            )
        for test_snippet, expected in test_fixtures:
            self.assertEqual(url_quote(test_snippet), expected)

    @unittest.skipIf(platform.system() == "Windows", "POSIX paths")
    def test_quote_absolute_path(self):
        # Python 3.14's pathname2url() returns "///tmp/foo" for "/tmp/foo";
        # url_quote must keep returning the same as on Python 3.13 and earlier.
        test_fixtures = [
            ["/", "/"],
            ["/tmp/foo", "/tmp/foo"],
            ["/tmp/foo bar/egg", "/tmp/foo%20bar/egg"],
            ["/tmp/abc:test", "/tmp/abc%3Atest"],
        ]
        for test_snippet, expected in test_fixtures:
            self.assertEqual(url_quote(test_snippet), expected)

    @unittest.skipIf(platform.system() != "Windows", "Windows paths")
    def test_quote_absolute_path_windows(self):
        test_fixtures = [
            ["\\foo bar\\test.txt", "/foo%20bar/test.txt"],
            ["/foo bar/test.txt", "/foo%20bar/test.txt"],
            ["D:\\", "D:/"],
            ["\\\\server\\share\\test.txt", "//server/share/test.txt"],
        ]
        for test_snippet, expected in test_fixtures:
            self.assertEqual(url_quote(test_snippet), expected)

    def test_quote_with_python314_pathname2url(self):
        # Simulate Python 3.14's pathname2url(), which adds an empty
        # authority ("//") in front of every absolute path, on any Python.
        original = six.moves.urllib.request.pathname2url

        def pathname2url(path):
            url = original(path)
            if url.startswith("/") and not url.startswith("///"):
                url = "//" + url
            return url

        with mock.patch.object(
            six.moves.urllib.request, "pathname2url", pathname2url
        ):
            self.assertEqual(url_quote("foo/bar ha"), "foo/bar%20ha")
            self.assertEqual(url_quote("/foo/bar ha"), "/foo/bar%20ha")
            if platform.system() == "Windows":
                self.assertEqual(url_quote("C:\\foo bar"), "C:/foo%20bar")

    @unittest.skipIf(platform.system() == "Windows", "POSIX paths")
    def test_osfs_geturl_for_fs(self):
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        with OSFS(tmpdir) as fs:
            fs.writetext("foo bar.txt", "hi")
            url = fs.geturl("foo bar.txt", purpose="fs")
            self.assertEqual(
                url, "osfs://" + fs.getsyspath("foo bar.txt").replace(" ", "%20")
            )
            self.assertTrue(url.startswith("osfs:///"))
            self.assertFalse(url.startswith("osfs:////"))
