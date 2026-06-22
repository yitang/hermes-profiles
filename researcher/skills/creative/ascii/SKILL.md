---
name: ascii
description: "ASCII art creation: static banners (pyfiglet, figlet, lolcat), ASCII shapes (cowsay, boxes), image-to-ASCII conversion, and animated ASCII video/audio production."
version: 1.0.0
author: Hermes Agent (consolidated from ascii-art + ascii-video)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ASCII, Art, Banners, Creative, Animation, Video, Audio, Visualization]
    related_skills: [excalidraw, sketch]
---

# ASCII Art — Static & Animated

Create character-based visual output: static banners and shapes, image-to-ASCII conversion, and full animated ASCII video/audio production.

## 1. Static ASCII Art

### Text Banners (pyfiglet — local)

```bash
pip install pyfiglet
python3 -c "import pyfiglet; print(pyfiglet.figlet_format('Hello', font='slant'))"
```

Available fonts directory:
```bash
python3 -c "import pyfiglet; [print(f) for f in pyfiglet.FigletFont.getFonts()]"
```

### Text Banners (figlet — system)

```bash
figlet "Hello World"
figlet -f slant "Hello"
figlet -f small -w 80 "Wide text"
figlet -k "Kerning test"
```

List installed fonts:
```bash
showfigfonts -p $(figlet -I 1) 2>/dev/null | head -40
```

### Colorized Text (lolcat)

```bash
figlet "Hello" | lolcat
cowsay "Hello" | lolcat
```

### ASCII Speech (cowsay)

```bash
cowsay "Hello from Hermes"
cowsay -f dragon "I am a dragon"
cowsay -f tux "Linux rules"
```

List all cowfiles:
```bash
cowsay -l
```

### Box Drawing (boxes)

```bash
echo "Hello" | boxes
echo "Hello" | boxes -d boy
echo "Hello" | boxes -d columns
```

List all box designs:
```bash
boxes -l
```

### Image to ASCII (jp2a / chafa)

```bash
# jp2a — simple threshold-based
jp2a input.jpg
jp2a --width=80 --colors input.jpg

# chafa — high-quality color ASCII art
chafa input.png
chafa --symbols block --size 80x40 input.png
chafa --symbols all --colors 256 --animate true input.gif
```

## 2. Animated ASCII Video

Production pipeline for converting video/audio/generative input into colored ASCII character video output (MP4, GIF, image sequence).

### Core Tools

| Tool | Purpose | Install |
|------|---------|---------|
| **termimage** | Still image → ASCII | `cargo install termimage` or `pip install term-image` |
| **chafa** | High-quality image → ANSI/ASCII | `apt install chafa` or `brew install chafa` |
| **jp2a** | JPEG → ASCII (simple) | `apt install jp2a` or `brew install jp2a` |
| **FFmpeg** | Video frame extraction, audio, encoding | `apt install ffmpeg` |
| **ImageMagick** | Frame processing, GIF generation | `apt install imagemagick` |

### Video to ASCII Pipeline

```bash
# 1. Extract frames
ffmpeg -i input.mp4 -vf "fps=10,scale=80:40" frames/frame_%04d.png

# 2. Convert each frame to ASCII
for f in frames/*.png; do
  chafa --symbols block --colors 256 --size 80x40 "$f" > "ascii/$(basename $f).txt"
done

# 3. Re-encode to video
ffmpeg -framerate 10 -i ascii/frame_%04d.png.txt -c:v libx264 -pix_fmt yuv420p output.mp4
```

### Audio-Reactive ASCII

Use FFmpeg's showfreqs or showspectrum filters:
```bash
ffmpeg -i audio.mp3 -filter_complex "[0:a]showfreqs=s=640x480:mode=line:fscale=log" output.mp4
```

### Generative ASCII Animation

Use Python with pillow to generate frame sequences:
```python
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def render_frame(text_brightness_matrix, chars=" .:-=+*#%@", width=80):
    """Convert a brightness matrix to ASCII string."""
    result = []
    for row in text_brightness_matrix:
        line = "".join(chars[min(int(v * len(chars) / 256), len(chars)-1)] for v in row)
        result.append(line)
    return "\n".join(result)
```

## Verify

```bash
# Static
figlet "OK" && cowsay "ASCII ready"

# Video pipeline
ffmpeg -version && chafa --version
```
