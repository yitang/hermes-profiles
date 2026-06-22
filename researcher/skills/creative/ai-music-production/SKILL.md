---
name: ai-music-production
description: "AI music creation: songwriting craft and Suno AI prompt engineering, plus open-source HeartMuLa local music generation (HeartCodec, HeartTranscriptor)."
version: 1.0.0
author: Hermes Agent (consolidated from songwriting-and-ai-music + heartmula)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [music, songwriting, suno, ai-music, heartmula, lyrics, generation]
    related_skills: [audiocraft]
---

# AI Music Production — Craft & Generation

Two approaches to AI-assisted music creation, chosen by workflow:

| Approach | Best For | Requirements |
|----------|----------|-------------|
| **Songwriting & Suno Prompts** | Crafting lyrics, structuring songs, creating Suno prompt tags | None (creative/theory) |
| **HeartMuLa** (local generation) | Open-source music generation from lyrics + tags, offline | GPU 8GB+ VRAM |

## 1. Songwriting & Suno Prompt Engineering

### Song Structure Guidelines

- Verses: ~8 lines each, set the scene/narrative
- Chorus: 4-6 lines, emotional core, repeated
- Bridge: Shift in perspective or key, 4-8 lines
- Outro: Fade out, tag, or resolution

### Lyric Crafting

- Show, don't tell (specific images > abstract feelings)
- Internal rhymes strengthen flow
- Consistent meter per section (match syllable counts)
- Leave space for melody — not every beat needs a word

### Suno AI Prompt Tags

```text
[Genre: pop/rock/electronic/folk/etc.]
[Mood: melancholic/upbeat/dark/whimsical]
[Vocal: male/female/duet/choir]
[Instrument: acoustic guitar, piano, strings, 808s]
[Tempo: slow/medium/fast]
[Key: Am/C/Dmaj/etc.]

[Lyrics]
Verse 1:
...
Chorus:
...
```

### Song Formats for Suno

- **Standard song**: Verse-Chorus-Verse-Chorus-Bridge-Chorus
- **Folk/ballad**: Verse-Verse-Chorus-Verse-Chorus
- **Electronic**: Build-Drop-Build-Drop-Bridge-Outro
- **Parody**: Match original structure exactly, replace content

## 2. HeartMuLa (Local Open-Source Music Generation)

### Quick Start

```bash
pip install heartmula
heartmula --lyrics "Your lyrics here" --tags "pop, female vocal" --output song.wav
```

### Hardware
- Minimum: 8GB VRAM with `--lazy_load true`
- Recommended: 16GB+ VRAM
- Multi-GPU: `--mula_device cuda:0 --codec_device cuda:1`

### Model Family
- **HeartMuLa** — Music language model (3B/7B) for generation from lyrics + tags
- **HeartCodec** — 12.5Hz music codec for high-fidelity audio
- **HeartTranscriptor** — Whisper-based lyrics transcription
- **HeartCLAP** — Audio-text alignment model

### Key Flags

| Flag | Purpose |
|------|---------|
| `--lazy_load true` | Load/unload models sequentially (lower VRAM) |
| `--output wav` | Output format (wav, mp3, flac) |
| `--duration 30` | Output duration in seconds |
| `--temperature 0.9` | Sampling temperature |
| `--top_k 250` | Top-k sampling for diversity |
