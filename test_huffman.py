import random

import pytest

from huffman import canonical_codes, code_lengths, compress, decompress, entropy

TEXT = ("It was the best of times, it was the worst of times, it was the age of wisdom, "
        "it was the age of foolishness. ").encode() * 50


@pytest.mark.parametrize("data", [
    b"",
    b"a" * 1000,
    random.Random(0).randbytes(20000),
    TEXT,
], ids=["empty", "repeated", "random", "text"])
def test_roundtrip(data):
    assert decompress(compress(data)) == data


def test_text_compresses_near_entropy():
    lengths = code_lengths(TEXT)
    avg = sum(lengths[b] for b in TEXT) / len(TEXT)
    h = entropy(TEXT)
    assert h <= avg < h + 1
    assert len(compress(TEXT)) < len(TEXT) * 0.7


@pytest.mark.parametrize("data", [TEXT, random.Random(1).randbytes(5000), bytes(range(256)) + b"zz" * 300])
def test_canonical_codes_prefix_free(data):
    codes = list(canonical_codes(code_lengths(data)).values())
    for i, a in enumerate(codes):
        for j, b in enumerate(codes):
            if i != j:
                assert not b.startswith(a)
    # a full Huffman tree satisfies Kraft with equality
    assert sum(2.0 ** -len(c) for c in codes) == pytest.approx(1.0)
