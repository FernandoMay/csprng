# csprng

Cryptographic-quality entropy extractor from video frames (LSB-based) with a **zero-dependency, fully testable core**.

## Qué hace

Extrae entropía de los *least significant bits* de una región de interés (ROI) de frames de video y deriva una clave de 256 bit hasheando con SHA-256.

## Estado del revival (2026-10)

- **🔓 Core separado de OpenCV**: la lógica de entropía (`extract_lsb_bits`, `bits_to_sha256`, `bit_entropy`) opera sobre *cualquier* secuencia de enteros de 8 bit → los tests corren **sin cámara, sin NumPy, sin OpenCV**.
- **💉 Inyección de dependencias**: `generate_key_from_frame(..., to_gray=...)` permite testear el pipeline completo sin cv2.
- **🧪 15 tests** (stdlib `unittest`, cero dependencias) + self-test de entropía sin cámara.
- **🧠 Métrica de entropía de Shannon por bit** incluida (~0 = sesgado, ~1 = aleatorio).
- **🔀 Derivación multi-frame**: `derive_key_from_many_frames()` mezcla entropía de N frames (más robusto que single-frame).
- **📦 Licencia MIT** y CLI (`--self-test` / `--camera`).

> El self-test usa `secrets.token_bytes` del OS como referencia de alta entropía: verificá que la métrica dé ~1.0 antes de confiar en una fuente física.

## Requisitos

- **Core + tests**: Python 3.8+, **cero dependencias**.
- **Modo cámara**: `opencv-python` (`pip install opencv-python`). NumPy se instala como dependencia de OpenCV.

## Uso

```bash
python csprng.py --self-test        # métricas de entropía, sin cámara
python csprng.py --camera           # demo con la cámara (Ctrl+C para parar)
```

Uso programático:

```python
from csprng import generate_key_from_frame, derive_key_from_many_frames

# Un frame
key = generate_key_from_frame(frame, roi_coords=(0, 0, 320, 240), block_size=256)

# O más robusto: mezclando N frames
key, bits = derive_key_from_many_frames(frames, (0, 0, 320, 240), frame_count=8)
```

## Tests

```bash
python -m unittest discover -s tests -v
```

Cubren: extracción de LSBs, conteo insuficiente, derivación SHA-256 determinista, métrica de entropía (constante → 0, alternante → 1), validación de frames inválidos y ROI negativo, inyección de `to_gray`.

## ⚠️ Limitaciones honestas

- El LSB de frames de webcam **puede tener baja entropía real**: muchos sensores aplican corrección de píxeles, compresión o quemado de patrón fijo. Medí antes de confiar (`bit_entropy`).
- Single-frame + hash directo es un PoC. Para uso real: multi-frame, tests formales de aleatoriedad (NIST SP 800-22) y health checks continuos.
- **No reemplaza** al CSPRNG del sistema (`secrets`, `os.urandom`) — es un experimento didáctico.

## Licencia

MIT — ver [LICENSE](LICENSE).

## Autor

[FernandoMay](https://github.com/FernandoMay)
