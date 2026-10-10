"""Test suite for csprng. Zero dependencies — runs on the stdlib alone.

    python -m unittest discover -s tests -v
"""
import unittest

from csprng import (
    bit_entropy,
    bits_to_sha256,
    extract_lsb_bits,
    generate_key_from_frame,
    derive_key_from_many_frames,
)


class TestExtractLsb(unittest.TestCase):
    def test_extracts_lsb_only(self):
        # 0b10101010 → LSB 0 ; 0b01010101 → LSB 1
        self.assertEqual(extract_lsb_bits([0b10101010, 0b01010101], 2),
                         "01")
        self.assertEqual(extract_lsb_bits([0b10101010, 0b01010101, 0xFF, 0x00], 4),
                         "0110")

    def test_respects_count(self):
        data = bytes(range(256))
        self.assertEqual(len(extract_lsb_bits(data, 16)), 16)

    def test_insufficient_data_returns_none(self):
        self.assertIsNone(extract_lsb_bits(b"\x01\x02", 100))

    def test_works_with_any_int_iterable(self):
        self.assertEqual(extract_lsb_bits([1, 0], 2), "10")

    def test_numpy_compatible(self):
        # objects exposing __iter__ of ints work without importing numpy.
        class FakeUint8Array:
            def __iter__(self):
                return iter([0xFF, 0x00, 0x01, 0x01])
        self.assertEqual(extract_lsb_bits(FakeUint8Array(), 4), "1011")


class TestShaDerivation(unittest.TestCase):
    def test_key_is_64_hex_chars(self):
        key = bits_to_sha256("0101" * 16)
        self.assertEqual(len(key), 64)
        int(key, 16)  # raises if not valid hex

    def test_deterministic(self):
        bits = "11001010" * 32
        self.assertEqual(bits_to_sha256(bits), bits_to_sha256(bits))

    def test_different_bits_different_keys(self):
        self.assertNotEqual(bits_to_sha256("0" * 256), bits_to_sha256("1" * 256))


class TestEntropyMetric(unittest.TestCase):
    def test_constant_bits_zero_entropy(self):
        self.assertAlmostEqual(bit_entropy("0" * 1000), 0.0)

    def test_alternating_bits_max_entropy(self):
        self.assertAlmostEqual(bit_entropy("01" * 500), 1.0)

    def test_empty_is_zero(self):
        self.assertEqual(bit_entropy(""), 0.0)


class TestFrameApi(unittest.TestCase):
    """generate_key_from_frame accepts an injected to_gray so the core is
    exercised without importing OpenCV."""

    class _FakeRoi:
        def __init__(self, values):
            self._values = values
        @property
        def size(self):
            return len(self._values)

    class _FakeFrame:
        def __init__(self, n_values):
            self._values = list(range(n_values))
        @property
        def size(self):
            return len(self._values)
        def __getitem__(self, key):
            return TestFrameApi._FakeRoi(self._values)

    def test_valid_frame_derives_hex_key(self):
        key = generate_key_from_frame(self._FakeFrame(600), (0, 0, 320, 240),
                                      256, to_gray=lambda roi: roi._values)
        self.assertEqual(len(key), 64)
        int(key, 16)

    def test_same_frame_same_key(self):
        frame = self._FakeFrame(600)
        k1 = generate_key_from_frame(frame, (0, 0, 320, 240), 256,
                                     to_gray=lambda roi: roi._values)
        k2 = generate_key_from_frame(frame, (0, 0, 320, 240), 256,
                                     to_gray=lambda roi: roi._values)
        self.assertEqual(k1, k2)

    def test_invalid_frames_return_none(self):
        self.assertIsNone(generate_key_from_frame(None, (0, 0, 10, 10)))
        self.assertIsNone(generate_key_from_frame(self._FakeFrame(0), (0, 0, 1, 1)))

    def test_negative_roi_rejected(self):
        self.assertIsNone(
            generate_key_from_frame(self._FakeFrame(64), (-1, 0, 2, 2)))


if __name__ == "__main__":
    unittest.main()
