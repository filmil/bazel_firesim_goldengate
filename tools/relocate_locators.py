"""Makes the Chisel source locators in a jar relative to their repository.

Chisel 3.6's SourceInfo macro stores each locator as the source file's
canonical path, minus `chisel.project.root` (or `user.dir`) and a leading
slash.
Bazel's external repositories resolve under the output base, outside both, so
the jar would hold paths such as

    data/bazel/output/<hash>/external/+_repo_rules+firesim/sim/midas/X.scala

This tool rewrites each such locator to `sim/midas/X.scala`, the form Chisel's
own Maven jars have.
It edits the UTF8 entries of each class file's constant pool, and keeps every
other byte of the jar.

Usage: relocate_locators <in.jar> <sources.txt> <out.jar>

`sources.txt` lists the compiled Scala sources, one per line, as
`<canonical repository name>\t<path in the repository>`, with an empty
repository name for the main repository.
"""

import struct
import sys
import zlib

# Strings that show a build machine's Bazel tree in a locator; the
# locators_test checks for the same ones.
_MACHINE_MARKERS = (b"external/", b"execroot/", b"bazel-out/", b"/sandbox/",
                    b"bazel/output", b".cache/bazel",
                    b"cache/repos/v1/contents/")


def read_sources(path):
    """Returns {suffix: repo-relative path} for the listed sources.

    An external repository resolves under `<output base>/external/<name>/`,
    or under the repository contents cache, `.../contents/<hash>/<id>/`.
    So a locator ends in `/<name>/<path>`, or in `/<path>` only.
    A source of the main repository has the latter form.
    """
    suffixes = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            repo, rel = line.split("\t")
            rel_b = rel.encode("utf-8")
            suffixes[b"/" + rel_b] = rel_b
            if repo:
                suffixes[b"/" + repo.encode("utf-8") + b"/" + rel_b] = rel_b
    return suffixes


def relocate(value, suffixes):
    """Returns the repo-relative form of a locator, or None to keep it."""
    if not value.endswith(b".scala"):
        return None
    # The longest matching suffix is the most specific one: the one with the
    # repository name, when the path has it.
    pos = value.find(b"/")
    while pos >= 0:
        rel = suffixes.get(value[pos:])
        if rel is not None:
            return rel
        pos = value.find(b"/", pos + 1)
    return None


# Sizes of the constant pool entries other than UTF8, by tag.
_CP_SIZES = {3: 4, 4: 4, 5: 8, 6: 8, 7: 2, 8: 2, 9: 4, 10: 4, 11: 4, 12: 4,
             15: 3, 16: 2, 17: 4, 18: 4, 19: 2, 20: 2}


def rewrite_class(data, suffixes):
    """Returns (new class bytes or None if unchanged, list of UTF8 values).

    Only UTF8 entries that a String constant refers to are rewritten: a
    locator is a string literal, `SourceLine(<path>, <line>, <column>)`.
    """
    if data[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("not a class file")
    count = struct.unpack_from(">H", data, 8)[0]
    entries = {}  # index: (tag, raw entry bytes, or the value of a UTF8)
    strings = set()
    pos = 10
    index = 1
    while index < count:
        tag = data[pos]
        if tag == 1:
            length = struct.unpack_from(">H", data, pos + 1)[0]
            entries[index] = (tag, data[pos + 3:pos + 3 + length])
            pos += 3 + length
        else:
            size = _CP_SIZES[tag]
            entries[index] = (tag, data[pos:pos + 1 + size])
            if tag == 8:
                strings.add(struct.unpack_from(">H", data, pos + 1)[0])
            pos += 1 + size
            if tag in (5, 6):
                index += 1  # Long and Double take two slots.
        index += 1
    out = [data[:10]]
    values = []
    changed = False
    for index, (tag, raw) in entries.items():
        if tag != 1:
            out.append(raw)
            continue
        value = raw
        if index in strings:
            new = relocate(value, suffixes)
            if new is not None and new != value:
                changed = True
                value = new
        values.append(value)
        out.append(b"\x01" + struct.pack(">H", len(value)) + value)
    out.append(data[pos:])
    return (b"".join(out) if changed else None), values


def _central_directory(jar):
    """Yields the raw central directory records of a jar without zip64."""
    eocd = jar.rfind(b"PK\x05\x06")
    if eocd < 0:
        raise ValueError("no end of central directory")
    (_, disk, cd_disk, n_disk, n, cd_size, cd_offset,
     comment_len) = struct.unpack_from("<IHHHHIIH", jar, eocd)
    if disk or cd_disk or n_disk != n or n == 0xFFFF or \
            0xFFFFFFFF in (cd_size, cd_offset):
        raise ValueError("multi-disk or zip64 jars are not supported")
    pos = cd_offset
    for _ in range(n):
        if jar[pos:pos + 4] != b"PK\x01\x02":
            raise ValueError("bad central directory record")
        name_len, extra_len, comment_len2 = struct.unpack_from(
            "<HHH", jar, pos + 28)
        end = pos + 46 + name_len + extra_len + comment_len2
        yield jar[pos:end]
        pos = end
    yield jar[eocd + 22:eocd + 22 + comment_len]  # The jar comment.


def _local_span(jar, offset, flags, csize):
    """Returns the end of the local entry at `offset`, data descriptor too."""
    name_len, extra_len = struct.unpack_from("<HH", jar, offset + 26)
    end = offset + 30 + name_len + extra_len + csize
    if flags & 0x8:
        end += 16 if jar[end:end + 4] == b"PK\x07\x08" else 12
    return end


def relocate_jar(jar, suffixes):
    """Returns (new jar bytes, number of classes rewritten, leftovers)."""
    records = list(_central_directory(jar))
    comment = records.pop()
    local_out = []
    central_out = []
    offset = 0
    rewritten = 0
    leftovers = []
    for rec in records:
        (flags, method, crc, csize, usize, name_len, extra_len,
         local_offset) = (struct.unpack_from("<H", rec, 8)[0],
                          struct.unpack_from("<H", rec, 10)[0],
                          *struct.unpack_from("<III", rec, 16),
                          *struct.unpack_from("<HH", rec, 28),
                          struct.unpack_from("<I", rec, 42)[0])
        name = rec[46:46 + name_len]
        end = _local_span(jar, local_offset, flags, csize)
        local = jar[local_offset:end]
        if name.endswith(b".class"):
            lname, lextra = struct.unpack_from("<HH", local, 26)
            body = local[30 + lname + lextra:30 + lname + lextra + csize]
            if method == 8:
                body = zlib.decompress(body, -15)
            elif method != 0:
                raise ValueError("unsupported compression in %r" % name)
            new_body, values = rewrite_class(body, suffixes)
            if new_body is not None:
                if lextra or extra_len:
                    # Zip64 or alignment data would no longer fit the entry.
                    raise ValueError("extra fields in %r" % name)
                rewritten += 1
                # A rewritten class is stored, not deflated: its bytes then
                # depend on no zlib build.
                crc = zlib.crc32(new_body)
                size = len(new_body)
                flags &= ~0x8
                header = bytearray(local[:30 + lname + lextra])
                struct.pack_into("<HH", header, 6, flags, 0)
                struct.pack_into("<III", header, 14, crc, size, size)
                local = bytes(header) + new_body
                rec = bytearray(rec)
                struct.pack_into("<HH", rec, 8, flags, 0)
                struct.pack_into("<III", rec, 16, crc, size, size)
                rec = bytes(rec)
                values = rewrite_class(new_body, {})[1]
            for v in values:
                if v.endswith(b".scala") and any(
                        m in v for m in _MACHINE_MARKERS):
                    leftovers.append((name.decode("utf-8"), v.decode(
                        "utf-8", "replace")))
        rec = bytearray(rec)
        struct.pack_into("<I", rec, 42, offset)
        central_out.append(bytes(rec))
        local_out.append(local)
        offset += len(local)
    central = b"".join(central_out)
    eocd = struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, len(records),
                       len(records), len(central), offset, len(comment))
    return (b"".join(local_out) + central + eocd + comment, rewritten,
            leftovers)


def main(argv):
    if len(argv) != 4:
        sys.exit(__doc__)
    with open(argv[1], "rb") as f:
        jar = f.read()
    suffixes = read_sources(argv[2])
    out, rewritten, leftovers = relocate_jar(jar, suffixes)
    if leftovers:
        for name, value in leftovers[:20]:
            print("%s: %s" % (name, value), file=sys.stderr)
        sys.exit("%d locators still hold a Bazel path; is a source missing "
                 "from %s?" % (len(leftovers), argv[2]))
    if not rewritten:
        sys.exit("no locator was rewritten; the source list is likely wrong")
    with open(argv[3], "wb") as f:
        f.write(out)


if __name__ == "__main__":
    main(sys.argv)
