# csprng

Cryptographic-quality entropy extractor from video frames (LSB-based).

## Project

**csprng** is a small utility that extracts entropy from live camera frames and derives a 256-bit key by hashing least-significant-bits (LSBs) from a region of interest (ROI). It's intended as an experimental proof-of-concept for deriving keys from physical video noise.

## Requirements

- **Python**: 3.8+
- **Packages**: OpenCV, NumPy

Install with pip (recommended) or via conda:

```bash
pip install opencv-python numpy
```

Or with conda:

```bash
conda install -c conda-forge opencv numpy
```

## Quick Start

Run the example script which captures frames from the default camera and prints derived keys:

```bash
python csprng.py
```

Press Ctrl+C to stop the script.

## How it works

- Capture a frame from the camera.
- Extract a rectangular Region Of Interest (ROI).
- Convert ROI to grayscale and take the least-significant bit (LSB) plane.
- Flatten LSBs into a bit string and hash the first N bits (default 256) with SHA-256.
- The SHA-256 hex digest is returned as the derived 256-bit key.

## Usage (API)

- `generate_key_from_frame(frame, roi_coords, block_size=256)`
	- `frame` — a NumPy array (BGR image) as returned by OpenCV.
	- `roi_coords` — tuple `(x, y, w, h)` defining the ROI rectangle.
	- `block_size` — number of raw bits to collect before hashing (default 256).
	- Returns: 64-character hex string (SHA-256) or `None` on error/insufficient entropy.

The example runner in `csprng.py` opens the default camera (index 0), uses ROI `(0, 0, 320, 240)`, and prints generated keys to stdout.

See the implementation: [csprng.py](csprng.py#L1-L200)

## Notes & Limitations

- This is experimental and should NOT be used as a drop-in replacement for production-grade CSPRNGs.
- Entropy quality depends heavily on camera noise, lighting, and ROI selection.
- The current method naively uses LSBs and a single-frame hash; for real-world use combine multiple frames and perform stronger entropy assessments.

## Contributing

Suggestions, bug reports, and improvements are welcome. Open an issue or send a patch.

## License

No license provided. Add a LICENSE file to make terms explicit.

