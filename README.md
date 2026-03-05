# Skript Reader Datkom

Converts a university lecture PDF into an accessible audiobook. Each slide is processed by a vision-language model to generate clean, TTS-friendly prose, which is then synthesized to speech and merged into a single audio file with chapter markers.

## Pipeline

```
merged.pdf → slides/*.png → results/texts/*.txt → results/audios/*.wav → results/merged/merged.ogg
```

1. **PDF → Images** (`src/pdf_to_slides.py`) — renders each PDF page to a PNG at 144 DPI using PyMuPDF
2. **Images → Text** (`src/slides_to_text.py`) — sends each slide to Gemini 2.0 Flash via Vertex AI; the model produces clean flowing prose suitable for TTS (no markdown, no bullet points, in German)
3. **Text → Audio** (`src/text_to_speech.py`) — synthesizes each text file using Gemini 2.5 Flash TTS (voice: Charon) and saves as WAV
4. **Merge** (`src/merge.py`) — concatenates all WAV files into a single Opus-encoded `.ogg` with embedded chapter markers (one chapter per slide)

Steps 2 and 3 are orchestrated by `main.py`. Step 1 and 4 are run separately.

## Requirements

- Python 3.12
- [uv](https://github.com/astral-sh/uv) (package manager)
- ffmpeg (for merging)
- A GCP project with Vertex AI enabled

## Setup

**1. Install dependencies**

```bash
uv sync
```

**2. Configure environment**

Create a `.env` file in the project root:

```env
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
```

**3. Enable GCP APIs**

The required APIs (Vertex AI, Text-to-Speech) can be enabled via Terraform:

```bash
cd terraform
terraform init
terraform apply -var="project_id=your-gcp-project-id"
```

Or enable them manually in the GCP console.

**4. Authenticate**

```bash
gcloud auth application-default login
```

## Usage

**Step 1 — Convert PDF to slide images** (run once)

Place your PDF as `merged.pdf` in the project root, then:

```bash
uv run python src/pdf_to_slides.py
```

This populates `slides/` with `slide_001.png`, `slide_002.png`, etc.

**Step 2 — Generate text and audio**

Configure the slide range and flags at the top of `main.py`:

```python
start_slide = 1
end_slide = 200
run_text_gen = True
run_audio_gen = True
```

Then run:

```bash
uv run python main.py
```

Both steps are idempotent — already-processed slides are skipped on re-runs.

**Step 3 — Merge audio files**

```bash
uv run python src/merge.py --start 1 --end 200
```

Output is written to `results/merged/`. Both the `.ogg` file and a `chapters.md` with timestamps are created.

## Output structure

```
results/
  texts/        # text{n}.txt — one file per slide
  audios/       # audio{n}.wav — one file per slide
  merged/       # merged.ogg + chapters.md
slides/         # slide_{nnn}.png — rendered PDF pages
```

## Resilience

- Both the text and audio generation steps retry automatically on transient errors (503, DNS failures, timeouts) with exponential backoff
- `main.py` aborts audio generation after 3 consecutive failures to surface quota or connectivity issues early
