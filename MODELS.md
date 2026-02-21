# AI Models

This document lists the selected models for each service category used in this project.

---

## 🧠 Chat / LLM (Ollama)

> Requires [Ollama](https://ollama.com) running at `localhost:11434`. All models support tool/function calling.

| # | Model | Ollama Tag | Size | Notes |
|---|-------|-----------|------|-------|
| 1 | **Llama 3.1 8B** | `llama3.1:8b` | ~4.7 GB | **Default.** Meta's flagship open model; native tool calling; strong reasoning |
| 2 | **Mistral Nemo 12B** | `mistral-nemo:12b` | ~7.1 GB | Mistral AI + NVIDIA; 128k context; excellent function calling |
| 3 | **Qwen 2.5 7B** | `qwen2.5:7b` | ~4.7 GB | Alibaba; outstanding coding and tool use; beats larger models on benchmarks |

**Install:**
```bash
ollama pull llama3.1:8b
ollama pull mistral-nemo:12b
ollama pull qwen2.5:7b
```

**Config (`config/default_config.json`):**
```json
"chat": {
  "default": "llama3.1:8b",
  "ollama_url": "http://localhost:11434"
}
```

---

## 🎨 Image Generation (Automatic1111 — SDXL Checkpoints)

> Requires [Automatic1111](https://github.com/AUTOMATIC1111/stable-diffusion-webui) running at `localhost:7860`.
> Place `.safetensors` files in `stable-diffusion-webui/models/Stable-diffusion/`.
> SDXL is optimised for **1024×1024** resolution.

| # | Model | Source | Size | Notes |
|---|-------|--------|------|-------|
| 1 | **Juggernaut XL v9** | [CivitAI](https://civitai.com/models/133005/juggernaut-xl) | ~6.9 GB | **Default.** Most popular photorealistic SDXL checkpoint; great for portraits and environments |
| 2 | **SDXL Base 1.0** | [HuggingFace](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0) | ~6.9 GB | Official Stability AI release; versatile foundation model |
| 3 | **DreamShaper XL 1.0** | [CivitAI](https://civitai.com/models/112902/dreamshaper-xl) | ~6.9 GB | Handles both photorealistic and artistic/fantasy styles |

**Config (`config/default_config.json`):**
```json
"image": {
  "default": "juggernautXL_v9.safetensors",
  "auto1111_url": "http://localhost:7860",
  "save_path": "./backend/storage/data/images"
}
```

---

## 🔊 TTS — Text-to-Speech (Piper)

> Requires [Piper](https://github.com/rhasspy/piper) installed at the configured `piper_path`.
> Each voice needs two files: `<voice>.onnx` and `<voice>.onnx.json`.
> Download from [HuggingFace rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices).

| # | Voice | Tag | Quality | Notes |
|---|-------|-----|---------|-------|
| 1 | **Ryan (Male, US English)** | `en_US-ryan-high` | High | **Default.** Expressive, natural-sounding; best for longer passages |
| 2 | **Lessac (Male, US English)** | `en_US-lessac-medium` | Medium | Clear and neutral; reliable general-purpose voice |
| 3 | **Amy (Female, US English)** | `en_US-amy-medium` | Medium | Natural female voice; good contrast to male voices |

**Install** — download both files for each voice and place them in the `piper/` directory:

| Voice | ONNX file | Config file |
|-------|-----------|-------------|
| Ryan high | `en_US-ryan-high.onnx` | `en_US-ryan-high.onnx.json` |
| Lessac medium | `en_US-lessac-medium.onnx` | `en_US-lessac-medium.onnx.json` |
| Amy medium | `en_US-amy-medium.onnx` | `en_US-amy-medium.onnx.json` |

Voice files: [huggingface.co/rhasspy/piper-voices/tree/main/en/en_US](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US)

**Config (`config/default_config.json`):**
```json
"tts": {
  "default_voice": "en_US-ryan-high",
  "piper_path": "./piper"
}
```

---

## Summary

| Category | Default Model | Service |
|----------|--------------|---------|
| Chat / LLM | `llama3.1:8b` | Ollama |
| Image Generation | `juggernautXL_v9.safetensors` | Automatic1111 |
| TTS | `en_US-ryan-high` | Piper |
