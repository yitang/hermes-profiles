# Tesseract OCR Spike Reference

Quick-start guide for running Tesseract OCR in a disposable spike.

## Setup (no root)

If tesseract isn't installed on the host, use Docker Alpine:

```bash
docker run --rm alpine:latest sh -c \
  "apk add --no-cache tesseract-ocr tesseract-ocr-data-eng >/dev/null 2>&1 && \
   tesseract --version"
```

To OCR an image mounted from the host:

```bash
docker run --rm \
  -v /path/to/images:/img:ro \
  alpine:latest sh -c \
  "apk add --no-cache tesseract-ocr tesseract-ocr-data-eng >/dev/null 2>&1 && \
   tesseract /img/sign.png stdout -l eng --psm 6"
```

## Key Parameters

| Flag | Usage |
|------|-------|
| `-l eng` | English language data (or `eng+fra` for multi-lang) |
| `--psm 6` | Assumes uniform text block — best for signs, labels |
| `--psm 3` | Fully automatic page segmentation (default) |
| `stdout` | Output to stdout instead of a file |

## PSM Modes for Signs

| Mode | Best for |
|------|----------|
| `3` | Default auto — general purpose |
| `6` | **Uniform block of text** — parking signs, labels, single paragraphs |
| `7` | Single line of text |
| `8` | Single word |
| `11` | Sparse text with no particular order |

## Preprocessing Pipeline

The correct order matters. Test with and without each step:

```python
from PIL import Image, ImageFilter, ImageOps

img = Image.open(path)

# 1. Grayscale
if img.mode != "L":
    img = img.convert("L")

# 2. Gentle contrast stretch (NOT aggressive)
img = ImageOps.autocontrast(img, cutoff=3)

# 3. Light sharpen
img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=80, threshold=2))

# DO NOT binarize — aggressive thresholding (e.g. all pixels > 128 → 255)
# destroys thin text. Grayscale is fine for Tesseract 5.x.
```

## Pitfalls

- **Aggressive binarization kills readability.** The old threshold-at-128 pattern destroys thin sign text. Keep it grayscale.
- **Docker image `tesseractshadow/tesseract` does not exist.** Use `alpine:latest` with apk instead.
- **`pip install --break-system-packages` may work** on Dev machines, but Docker is more portable.
- **Install both packages:** `tesseract-ocr` (engine) + `tesseract-ocr-data-eng` (language data). Missing = "Failed loading language 'eng'".
- **At 6m+ simulated distance** Gaussian blur kills OCR completely. Real-world users walk closer to read signs.
- **Font choice matters.** The UK Transport typeface is standard on UK traffic signs; DejaVu Sans is a reasonable substitute for synthetic tests.

## Verdict Format for OCR Spikes

```markdown
## Verdict: VALIDATED | PARTIAL | INVALIDATED

| Distance | Type Accuracy | Hours Accuracy | Max Stay Accuracy |
|----------|:------------:|:--------------:|:-----------------:|
| 2m       | X%           | X%             | X%                |
| 4m       | X%           | X%             | X%                |

At realistic distances (2-4m), all targets met/exceeded.
```
