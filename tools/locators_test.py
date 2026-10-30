"""Checks that a jar's class files hold no Bazel path of the build machine.

Usage: locators_test <jar> <a locator the jar must hold>

The scan reads raw class bytes, not only constant pool entries, so it also
finds a path in places the rewrite does not touch.
"""

import re
import sys
import unittest
import zipfile

# A `.scala` path that runs through a Bazel tree: an output base, an exec
# root, a sandbox, an output directory or the repository contents cache.
_BAZEL_PATH = re.compile(
    rb"(?:external/|execroot/|bazel-out/|/sandbox/|bazel/output|"
    rb"\.cache/bazel|cache/repos/v1/contents/)[\x21-\x7e]*?\.scala")


class LocatorsTest(unittest.TestCase):
    jar = None
    expected = None

    def test_no_bazel_paths(self):
        found = []
        seen = False
        with zipfile.ZipFile(self.jar) as z:
            for info in z.infolist():
                if not info.filename.endswith(".class"):
                    continue
                data = z.read(info)
                seen = seen or self.expected in data
                found += [(info.filename, m) for m in _BAZEL_PATH.findall(data)]
        self.assertEqual(found[:20], [])
        self.assertTrue(seen, "no class holds the locator %r" % self.expected)


if __name__ == "__main__":
    LocatorsTest.jar = sys.argv[1]
    LocatorsTest.expected = sys.argv[2].encode("utf-8")
    unittest.main(argv=sys.argv[:1])
