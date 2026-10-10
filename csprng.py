"""csprng — entropy extraction from video frames (LSB-based).

Pure-Python core (zero dependencies) + optional OpenCV camera front-end.

The entropy core works on *any* sequence of 8-bit values, which makes it
fully testable without a camera, NumPy or OpenCV installed.
"""
import argparse
import hashlib
import math
import secrets
import sys
from collections import Counter

DEFAULT_BLOCK_SIZE = 256


def extract_lsb_bits(values, count):
    """Return the first ``count`` least-significant bits of ``values``.

    ``values`` is any iterable of 8-bit ints (bytes, bytearray, NumPy uint8
    array, ...). Returns a string of '0'/'1', or None if not enough data.
    """
    bits = []
    for value in values:
        bits.append("1" if (value & 1) else "0")
        if len(bits) >= count:
            break
    if len(bits) < count:
        return None
    return "".join(bits)


def bits_to_sha256(bits):
    """Whiten a bit string into a 256-bit key via SHA-256."""
    return hashlib.sha256(bits.encode("ascii")).hexdigest()


def bit_entropy(bits):
    """Shannon entropy per bit, in [0.0, 1.0]. 1.0 = perfectly random."""
    if not bits:
        return 0.0
    counts = Counter(bits)
    n = len(bits)
    return max(0.0, -sum((c / n) * math.log2(c / n) for c in counts.values()))


def generate_key_from_frame(frame, roi_coords, block_size=DEFAULT_BLOCK_SIZE,
                            to_gray=None):
    """Derive a 256-bit key from one BGR video frame.

    Args:
        frame: NumPy array (H, W, 3) BGR, as returned by cv2.VideoCapture.
        roi_coords: (x, y, w, h) region of interest.
        block_size: raw bits to collect before hashing (default 256).
        to_gray: optional callable converting the ROI to an iterable of
            8-bit values. Defaults to OpenCV BGR2GRAY (imported lazily).
            Injected in tests so the core runs without OpenCV installed.

    Returns:
        64-char hex string, or None if the frame is invalid or the ROI
        does not contain enough bits.
    """
    if frame is None or getattr(frame, "size", 0) == 0:
        return None

    x, y, w, h = roi_coords
    if min(roi_coords) < 0:
        return None
    roi = frame[y:y + h, x:x + w]
    if getattr(roi, "size", 0) == 0:
        return None

    if to_gray is None:
        import cv2  # lazy: only needed for the camera front-end
        to_gray = lambda img: cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = to_gray(roi)
    bits = extract_lsb_bits(gray, block_size)
    if bits is None:
        return None
    return bits_to_sha256(bits)


def derive_key_from_many_frames(frames, roi_coords, frame_count,
                                block_size_per_frame=DEFAULT_BLOCK_SIZE):
    """Stronger key: mix LSB entropy from multiple frames.

    Collects ``block_size_per_frame`` bits from each of the first
    ``frame_count`` frames and hashes the concatenation once.

    Returns (hex_key, total_bits) or (None, 0) if any frame fails.
    """
    collected = []
    for i, frame in enumerate(frames):
        if i >= frame_count:
            break
        import cv2  # lazy
        if frame is None or getattr(frame, "size", 0) == 0:
            return None, 0
        x, y, w, h = roi_coords
        roi = frame[y:y + h, x:x + w]
        if roi.size == 0:
            return None, 0
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        bits = extract_lsb_bits(gray.reshape(-1), block_size_per_frame)
        if bits is None:
            return None, 0
        collected.append(bits)
    if len(collected) < frame_count:
        return None, 0
    return bits_to_sha256("".join(collected)), frame_count * block_size_per_frame


def camera_loop(roi=(0, 0, 320, 240), block_size=DEFAULT_BLOCK_SIZE):
    """Interactive demo: derive keys from the default camera until Ctrl+C."""
    import cv2  # lazy

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: cannot open camera.", file=sys.stderr)
        return 1

    print(f"Generating keys from camera ROI={roi} — press Ctrl+C to stop.")
    keys = set()
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Failed to grab frame.")
                break
            key = generate_key_from_frame(frame, roi, block_size)
            if key:
                print(f"Generated Secure Key: {key}")
                keys.add(key)
    except KeyboardInterrupt:
        print(f"\nStopped. {len(keys)} unique keys generated.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
    return 0


def self_test(n_bits=4096):
    """Dependency-free entropy self-check using the OS CSPRNG as a reference.

    Shows the extractor + entropy metrics working on data with (a) known
    low entropy and (b) high entropy — no camera required.
    """
    print("=== csprng self-test (no camera needed) ===")

    # Low-entropy source: all zeros
    zero_bits = "0" * n_bits
    print(f"all-zero bits    → entropy {bit_entropy(zero_bits):.3f} bit/bit "
          f"(expected ~0.0)")

    # High-entropy source: OS CSPRNG bytes (1 LSB per byte)
    random_bytes = secrets.token_bytes(n_bits)
    rnd_bits = extract_lsb_bits(random_bytes, n_bits)
    print(f"os.urandom LSBs  → entropy {bit_entropy(rnd_bits):.3f} bit/bit "
          f"(expected ~1.0)")

    # Determinism check
    k1 = bits_to_sha256(rnd_bits)
    k2 = bits_to_sha256(rnd_bits)
    print(f"determinism      → {'OK' if k1 == k2 else 'FAIL'}")
    print(f"sample key       → {k1}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="csprng",
        description="LSB entropy extraction and SHA-256 key derivation.",
    )
    parser.add_argument("--self-test", action="store_true",
                        help="run dependency-free entropy self-check")
    parser.add_argument("--camera", action="store_true",
                        help="capture from the default camera (needs OpenCV)")
    parser.add_argument("--bits", type=int, default=DEFAULT_BLOCK_SIZE,
                        help="bits to collect per frame (default 256)")
    args = parser.parse_args(argv)

    if args.self_test or not (args.camera or args.self_test):
        self_test()
        return 0
    return camera_loop(block_size=args.bits)


if __name__ == "__main__":
    raise SystemExit(main())
