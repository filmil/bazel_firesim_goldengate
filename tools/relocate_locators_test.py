"""Unit tests for relocate_locators, on a hand-built class file and jar."""

import io
import struct
import unittest
import zipfile

import relocate_locators as rl

SUFFIXES = {b"/+r/src/A.scala": b"src/A.scala", b"/src/A.scala": b"src/A.scala",
            b"/+r/src/C.scala": b"src/C.scala", b"/src/C.scala": b"src/C.scala"}


def utf8(s):
    return b"\x01" + struct.pack(">H", len(s)) + s


def make_class():
    pool = [
        utf8(b"data/ob/external/+r/src/A.scala"),  # 1
        b"\x08" + struct.pack(">H", 1),  # 2: String -> 1
        b"\x05" + b"\x00" * 8,  # 3 and 4: a Long takes two slots
        utf8(b"data/ob/external/+r/src/B.scala"),  # 5: not a String
        b"\x08" + struct.pack(">H", 7),  # 6: String -> 7
        utf8(b"cache/repos/v1/contents/ab/12/src/C.scala"),  # 7
        utf8(b"/src/A.scala"),  # 8: not a String, kept
    ]
    return (b"\xca\xfe\xba\xbe\x00\x00\x00\x34" + struct.pack(">H", 9) +
            b"".join(pool) + b"TAIL")


class _NoSeek(io.RawIOBase):
    """A stream zipfile cannot seek in, so it writes data descriptors."""

    def __init__(self):
        self.buf = io.BytesIO()

    def writable(self):
        return True

    def write(self, b):
        return self.buf.write(b)


def make_jar(class_bytes, seekable=True):
    sink = io.BytesIO() if seekable else _NoSeek()
    with zipfile.ZipFile(sink, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("META-INF/MANIFEST.MF", b"Manifest-Version: 1.0\n")
        z.writestr("p/K.class", class_bytes)
        z.writestr("p/L.class", b"\xca\xfe\xba\xbe\x00\x00\x00\x34\x00\x01")
    return (sink if seekable else sink.buf).getvalue()


class RewriteClassTest(unittest.TestCase):

    def test_rewrites_string_constants_only(self):
        new, values = rl.rewrite_class(make_class(), SUFFIXES)
        self.assertEqual(values, [b"src/A.scala",
                                  b"data/ob/external/+r/src/B.scala",
                                  b"src/C.scala", b"/src/A.scala"])
        self.assertTrue(new.endswith(b"TAIL"))
        self.assertEqual(rl.rewrite_class(new, SUFFIXES)[0], None)

    def test_unchanged(self):
        self.assertEqual(rl.rewrite_class(make_class(), {})[0], None)


class RelocateJarTest(unittest.TestCase):

    def check(self, seekable):
        jar = make_jar(make_class(), seekable)
        if not seekable:
            self.assertTrue(zipfile.ZipFile(io.BytesIO(jar)).getinfo(
                "p/K.class").flag_bits & 0x8)
        out, rewritten, leftovers = rl.relocate_jar(jar, SUFFIXES)
        self.assertEqual(rewritten, 1)
        # B.scala is no String constant, so it is kept, and reported.
        self.assertEqual(leftovers,
                         [("p/K.class", "data/ob/external/+r/src/B.scala")])
        z = zipfile.ZipFile(io.BytesIO(out))
        self.assertIsNone(z.testzip())
        self.assertEqual(z.namelist(), ["META-INF/MANIFEST.MF", "p/K.class",
                                        "p/L.class"])
        self.assertEqual(z.read("p/K.class"),
                         rl.rewrite_class(make_class(), SUFFIXES)[0])
        self.assertEqual(z.getinfo("p/K.class").compress_type,
                         zipfile.ZIP_STORED)
        self.assertEqual(z.getinfo("p/L.class").compress_type,
                         zipfile.ZIP_DEFLATED)

    def test_seekable(self):
        self.check(True)

    def test_data_descriptors(self):
        self.check(False)

    def test_leftovers(self):
        _, rewritten, leftovers = rl.relocate_jar(make_jar(make_class()), {})
        self.assertEqual(rewritten, 0)
        self.assertEqual(leftovers, [
            ("p/K.class", "data/ob/external/+r/src/A.scala"),
            ("p/K.class", "data/ob/external/+r/src/B.scala"),
            ("p/K.class", "cache/repos/v1/contents/ab/12/src/C.scala")])


if __name__ == "__main__":
    unittest.main()
