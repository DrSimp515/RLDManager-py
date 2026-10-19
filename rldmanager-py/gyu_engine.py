# lang: Python, file: gyu_engine.py, target: cross-platform
# GYU image decoder — Python port of ImageGYU.cs from GARbro by morkt.
# Header: 'GYU\x1a', u16 flags @4, u16 comp @6, u32 key @8,
#         i32 bpp @12, w @16, h @20, datasize @24, alphasize @28, palsize @32.
# Compression: 0x0100 raw, 0x0200 LZ 4-arg mode 4, 0x0400 LZ 3-arg mode 2,
#             0x0800 LZ mode 0 (arg4=3). Obfuscation: MersenneTwister(key), 10 swaps.
# Alpha rule: (flags & 3) == 3 -> alpha as-is; else a>=0x10 ? 0xFF : a*0x10.
#
# Based on GARbro -- Copyright (C) 2015-2020 by morkt
# https://github.com/morkt/GARbro
# The MIT License (MIT)
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import struct


def lzss_decode(src, dst_size):
    N = 0x1000
    frame = bytearray(N)
    r = 0xFEE
    dst = bytearray()
    sp = 0
    remaining = len(src)
    src = bytes(src) + bytes(2)
    while remaining > 0 and len(dst) < dst_size:
        ctl = src[sp]; sp += 1; remaining -= 1
        bit = 1
        while bit != 0x100 and remaining > 0 and len(dst) < dst_size:
            if ctl & bit:
                b = src[sp]; sp += 1; remaining -= 1
                frame[r] = b; r = (r + 1) & 0xFFF
                dst.append(b)
            else:
                lo = src[sp]; hi = src[sp + 1]; sp += 2; remaining -= 2
                offset = ((hi & 0xF0) << 4) | lo
                count = 3 + (hi & 0xF)
                for _ in range(count):
                    v = frame[offset]; offset = (offset + 1) & 0xFFF
                    frame[r] = v; r = (r + 1) & 0xFFF
                    dst.append(v)
            bit <<= 1
    return bytes(dst[:dst_size])


def mersenne_deobfuscate(data, key):
    state = [0] * 624
    x = key & 0xFFFFFFFF
    for i in range(624):
        upper = x & 0xFFFF0000
        x = (69069 * x + 1) & 0xFFFFFFFF
        state[i] = upper | ((x & 0xFFFF0000) >> 16)
        x = (69069 * x + 1) & 0xFFFFFFFF
    idx = 624
    out = bytearray(data)
    n = len(out)
    if n == 0:
        return bytes(out)

    def mt():
        nonlocal idx
        if idx >= 624:
            for k in range(227):
                y = (state[k] & 0x80000000) | (state[k + 1] & 0x7FFFFFFF)
                v = state[k + 397] ^ (y >> 1)
                if y & 1:
                    v ^= 0x9908B0DF
                state[k] = v
            for k in range(227, 623):
                y = (state[k] & 0x80000000) | (state[k + 1] & 0x7FFFFFFF)
                v = state[k - 227] ^ (y >> 1)
                if y & 1:
                    v ^= 0x9908B0DF
                state[k] = v
            y = (state[623] & 0x80000000) | (state[0] & 0x7FFFFFFF)
            v = state[396] ^ (y >> 1)
            if y & 1:
                v ^= 0x9908B0DF
            state[623] = v
            idx = 0
        y = state[idx]; idx += 1
        y ^= y >> 11
        y ^= (y << 7) & 0x9D2C5680
        y ^= (y << 15) & 0xEFC60000
        y ^= y >> 18
        return y

    for _ in range(10):
        i1 = mt() % n
        i2 = mt() % n
        out[i1], out[i2] = out[i2], out[i1]
    return bytes(out)


def gyu_bits_decode(src, dst_size):
    dst = bytearray()
    dst.append(src[4])
    bitpos = 0
    bytepos = 5
    total = len(src) * 8

    def getbit():
        nonlocal bitpos, bytepos
        if bitpos >= total:
            return -1
        b = (src[bytepos] >> (7 - (bitpos & 7))) & 1
        bitpos += 1
        bytepos = bitpos >> 3
        return b

    def getbits(n):
        v = 0
        for _ in range(n):
            b = getbit()
            if b < 0:
                return -1
            v = (v << 1) | b
        return v

    def getbyte():
        nonlocal bytepos, bitpos
        if bitpos & 7:
            return getbits(8)
        if bytepos >= len(src):
            return -1
        b = src[bytepos]; bytepos += 1; bitpos += 8
        return b

    while len(dst) < dst_size:
        b = getbit()
        if b < 0:
            break
        if b == 1:
            c = getbyte()
            if c < 0:
                break
            dst.append(c)
            continue
        b2 = getbit()
        if b2 < 0:
            break
        if b2 == 1:
            c1 = getbyte(); c2 = getbyte()
            if c1 < 0 or c2 < 0:
                break
            count = (c1 << 8) | c2
            offset = (-1 << 13) | (count >> 3)
            count &= 7
            count = count + 1 if count else (getbyte() or 0)
        else:
            count = 1 + getbits(2)
            off = getbyte()
            if off < 0:
                break
            offset = (-1 << 8) | off
        src_idx = len(dst) + offset
        for _ in range(count + 1):
            dst.append(dst[src_idx]); src_idx += 1
    return bytes(dst)


def decode_gyu(data: bytes) -> tuple[bytes, int, int, int]:
    """Decode a GYU image. Returns (raw_pixels, width, height, bpp)."""
    assert data[:4] == b"GYU\x1a", "not a GYU file"
    flags, comp = struct.unpack_from("<HH", data, 4)
    key = struct.unpack_from("<I", data, 8)[0]
    bpp, w, h, datasize, alphasize, palsize = struct.unpack_from("<iiiiii", data, 12)
    payload = data[0x24:]
    packed = payload[:datasize]
    if key not in (0, 0xFFFFFFFF):
        packed = mersenne_deobfuscate(packed, key)
    stride = (w * bpp // 8 + 3) & ~3
    if comp == 0x0100:
        raw = packed
    elif comp == 0x0800:
        raw = gyu_bits_decode(packed, stride * h)
    else:
        raw = lzss_decode(packed, stride * h)
    return raw, w, h, bpp
