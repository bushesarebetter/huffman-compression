import argparse
import heapq
import math
import struct
from collections import Counter

MAGIC = b"HUF1"
# magic, original length, 256 code lengths (0 = symbol absent)
HEADER = struct.Struct(">4sQ256B")


def code_lengths(data):
    freq = Counter(data)
    if len(freq) == 1:
        return {next(iter(freq)): 1}
    lengths = dict.fromkeys(freq, 0)
    # (weight, tiebreak, symbols in subtree); every merge pushes those symbols one level deeper
    heap = [(f, s, [s]) for s, f in freq.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        f1, t1, a = heapq.heappop(heap)
        f2, t2, b = heapq.heappop(heap)
        for s in a + b:
            lengths[s] += 1
        heapq.heappush(heap, (f1 + f2, min(t1, t2), a + b))
    return lengths


def canonical_codes(lengths):
    codes, code, prev = {}, 0, 0
    for sym, n in sorted(lengths.items(), key=lambda kv: (kv[1], kv[0])):
        code <<= n - prev
        codes[sym] = format(code, f"0{n}b")
        code += 1
        prev = n
    return codes


def compress(data):
    lengths = code_lengths(data)
    table = [0] * 256
    for s, n in lengths.items():
        table[s] = n
    if not data:
        return HEADER.pack(MAGIC, 0, *table)
    codes = canonical_codes(lengths)
    bits = "".join(codes[b] for b in data)
    bits += "0" * (-len(bits) % 8)
    body = int(bits, 2).to_bytes(len(bits) // 8, "big")
    return HEADER.pack(MAGIC, len(data), *table) + body


def decompress(blob):
    magic, n, *table = HEADER.unpack_from(blob)
    if magic != MAGIC:
        raise ValueError("not a huffman file")
    if n == 0:
        return b""
    lengths = {s: L for s, L in enumerate(table) if L}
    # canonical decode: for each length, the first code and the symbols that use it
    by_len = {}
    for sym, L in sorted(lengths.items(), key=lambda kv: (kv[1], kv[0])):
        by_len.setdefault(L, []).append(sym)
    first, code, prev = {}, 0, 0
    for L in sorted(by_len):
        code <<= L - prev
        first[L] = code
        code += len(by_len[L])
        prev = L

    body = blob[HEADER.size:]
    bits = format(int.from_bytes(body, "big"), f"0{len(body) * 8}b")
    out = bytearray()
    code = length = 0
    for bit in bits:
        code = (code << 1) | (bit == "1")
        length += 1
        syms = by_len.get(length)
        if syms is not None and 0 <= code - first[length] < len(syms):
            out.append(syms[code - first[length]])
            if len(out) == n:
                break
            code = length = 0
    return bytes(out)


def entropy(data):
    n = len(data)
    return -sum(c / n * math.log2(c / n) for c in Counter(data).values()) if n else 0.0


def report(data, blob):
    n = len(data)
    print(f"original:   {n} bytes")
    print(f"compressed: {len(blob)} bytes ({HEADER.size} header + {len(blob) - HEADER.size} payload)")
    if n == 0:
        return
    lengths = code_lengths(data)
    avg = sum(lengths[b] for b in data) / n
    h = entropy(data)
    print(f"ratio:      {n / len(blob):.3f}x  ({len(blob) / n:.1%} of original)")
    print(f"entropy:    {h:.4f} bits/byte -> bound {math.ceil(h * n / 8)} bytes")
    print(f"huffman:    {avg:.4f} bits/byte ({avg - h:.4f} above entropy)")


def main():
    p = argparse.ArgumentParser(description="Canonical Huffman file compressor")
    p.add_argument("mode", choices=["compress", "decompress"])
    p.add_argument("src")
    p.add_argument("dst")
    args = p.parse_args()
    with open(args.src, "rb") as f:
        data = f.read()
    if args.mode == "compress":
        blob = compress(data)
        report(data, blob)
    else:
        blob = decompress(data)
    with open(args.dst, "wb") as f:
        f.write(blob)


if __name__ == "__main__":
    main()
