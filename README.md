# huffman-compression

A small file compressor using canonical Huffman codes. The header holds only the original length and one code length per byte value, so the decoder can rebuild the exact code table without storing the tree. Pure standard library.

## Setup

Python 3.10+, no dependencies.

## Run

```
python huffman.py compress input.txt input.huf
python huffman.py decompress input.huf restored.txt
```

Compressing prints the ratio and how close the codes get to the Shannon entropy. Running it on its own source:

```
original:   3738 bytes
compressed: 2493 bytes (268 header + 2225 payload)
ratio:      1.499x  (66.7% of original)
entropy:    4.7401 bits/byte -> bound 2215 bytes
huffman:    4.7619 bits/byte (0.0219 above entropy)
```

Random bytes don't compress (8.0 bits/byte, already at entropy), so the output ends up 268 bytes larger.

## Test

```
pip install pytest
python -m pytest -q
```

The tests round-trip an empty file, one repeated byte, random bytes and English text, and check that the canonical codes are prefix-free and satisfy Kraft's equality.
