#!/usr/bin/env python3
"""校验 StreetData 瓦片：magic byte、像素尺寸、片数、体积。

不依赖 PIL —— 只读文件头。PNG/WebP/JPEG 的尺寸都能从前几十字节拿到。
用法：python3 verify.py /data/StreetData [--sample 200]
"""
import base64
import json
import os
import random
import struct
import sys

# 瓦片边长：256 = 常规，512 = @2x。出 @2x 时用 `TILE_PX=512` 覆盖，
# 否则校验脚本会把全部瓦片误判成「尺寸不对」。
TILE = int(os.environ.get("TILE_PX", "256"))


def dims_webp(b):
    if b[:4] != b"RIFF" or b[8:12] != b"WEBP":
        return None
    fourcc = b[12:16]
    if fourcc == b"VP8 ":
        w, h = struct.unpack("<HH", b[26:30])
        return w & 0x3FFF, h & 0x3FFF
    if fourcc == b"VP8L":
        bits = struct.unpack("<I", b[21:25])[0]
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if fourcc == b"VP8X":
        w = int.from_bytes(b[24:27], "little") + 1
        h = int.from_bytes(b[27:30], "little") + 1
        return w, h
    return None


def dims_jpeg(b):
    if b[:3] != b"\xff\xd8\xff":
        return None
    i = 2
    while i < len(b) - 9:
        if b[i] != 0xFF:
            i += 1
            continue
        m = b[i + 1]
        if m in (0xC0, 0xC1, 0xC2, 0xC3):
            h, w = struct.unpack(">HH", b[i + 5:i + 9])
            return w, h
        if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    return None


def bits_of(b64, w, h):
    raw = base64.b64decode(b64)
    return raw, w * h


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    sample = int(sys.argv[2]) if len(sys.argv) > 2 else 200

    idx = json.load(open(os.path.join(root, "index.json")))
    print("version %s  bytes %.1f MB  split %s"
          % (idx["version"], idx["bytes"] / 1048576, idx["format_split"]))

    total = 0
    problems = []
    for zs, v in sorted(idx["zooms"].items(), key=lambda kv: int(kv[0])):
        z = int(zs)
        w, h = v["x1"] - v["x0"] + 1, v["y1"] - v["y0"] + 1
        present, _ = bits_of(v["present"], w, h)
        ext, _ = bits_of(v["ext_jpg"], w, h)
        n_present = sum(bin(b).count("1") for b in present)
        if n_present != v["count"]:
            problems.append("z%d 位图置位数 %d ≠ count %d" % (z, n_present, v["count"]))
        total += v["count"]
        print("  z%-3d %6d 片  %.1f KB  位图 %d×%d (%d B)"
              % (z, v["count"], v["bytes"] / 1024, w, h, len(present)))

    # 抽样校验文件头
    checked = bad = 0
    for zs, v in idx["zooms"].items():
        z = int(zs)
        w = v["x1"] - v["x0"] + 1
        h = v["y1"] - v["y0"] + 1
        present, _ = bits_of(v["present"], w, h)
        ext, _ = bits_of(v["ext_jpg"], w, h)
        coords = [(x, y) for y in range(h) for x in range(w)
                  if present[(y * w + x) >> 3] & (0x80 >> ((y * w + x) & 7))]
        for cx, cy in random.sample(coords, min(sample, len(coords))):
            x, y = v["x0"] + cx, v["y0"] + cy
            jpg = ext[(cy * w + cx) >> 3] & (0x80 >> ((cy * w + cx) & 7))
            ext_s = "jpg" if jpg else "webp"
            p = (os.path.join(root, "base", str(z), str(x >> 3), str(x), "%d.%s" % (y, ext_s))
                 if z >= 8 else os.path.join(root, "base", str(z), str(x), "%d.%s" % (y, ext_s)))
            checked += 1
            if not os.path.exists(p):
                problems.append("缺文件 %s" % p)
                bad += 1
                continue
            head = open(p, "rb").read(64)
            d = dims_webp(head) if ext_s == "webp" else dims_jpeg(head)
            if d is None:
                problems.append("magic byte 不对 %s" % p)
                bad += 1
            elif d != (TILE, TILE):
                problems.append("尺寸 %s = %s" % (p, d))
                bad += 1

    print("抽样 %d 片，异常 %d" % (checked, bad))
    print("index 声明 %d 片" % total)
    for p in problems[:20]:
        print("  ✗", p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
