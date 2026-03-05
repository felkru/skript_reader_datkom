# Project Rules

- **Regional Preference**: Always prioritize `europe-west1` (Belgium) for GCP services.
- **Model Availability Fallback**: If a specific model (e.g., Gemini 3 Flash Preview) is not available in `europe-west1`, use global endpoints and if that's not available use `us-central1`.
- **Model Selection**:
  - Use `gemini-3-flash-preview` for text generation from slides.
  - Use `gemini-2.5-flash-tts` for audio generation.
