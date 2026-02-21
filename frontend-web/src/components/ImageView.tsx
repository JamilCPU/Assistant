import { useState } from 'react';
import * as api from '../api/client';

export default function ImageView() {
  const [prompt, setPrompt] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [width, setWidth] = useState(512);
  const [height, setHeight] = useState(512);
  const [steps, setSteps] = useState(20);
  const [cfgScale, setCfgScale] = useState(7.0);
  const [generating, setGenerating] = useState(false);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim() || generating) return;
    setGenerating(true);
    setError(null);
    setImageUrl(null);

    try {
      const res = await api.generateImage({
        prompt: prompt.trim(),
        negative_prompt: negativePrompt.trim() || undefined,
        width,
        height,
        steps,
        cfg_scale: cfgScale,
      });
      // Use image_url if provided, otherwise fall back to image_path
      setImageUrl(res.image_url ?? res.image_path);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Image generation failed');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-8 py-6 flex flex-col gap-5">
        {/* Title */}
        <h2 className="text-lg font-semibold text-text-primary">Image Generation</h2>

        {/* Prompt */}
        <div>
          <label className="text-xs font-semibold text-text-secondary tracking-wide block mb-1">
            Prompt
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe the image you want to generate…"
            rows={3}
            className="w-full bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2.5 text-sm outline-none focus:border-border-light resize-none transition-colors placeholder:text-text-muted"
          />
        </div>

        {/* Negative prompt */}
        <div>
          <label className="text-xs font-semibold text-text-secondary tracking-wide block mb-1">
            Negative Prompt
          </label>
          <textarea
            value={negativePrompt}
            onChange={(e) => setNegativePrompt(e.target.value)}
            placeholder="Things to avoid in the image (optional)…"
            rows={2}
            className="w-full bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2.5 text-sm outline-none focus:border-border-light resize-none transition-colors placeholder:text-text-muted"
          />
        </div>

        {/* Parameters */}
        <div>
          <label className="text-xs font-semibold text-text-secondary tracking-wide block mb-2">
            Parameters
          </label>
          <div className="flex flex-wrap gap-6">
            <ParamInput label="Width" value={width} onChange={setWidth} min={64} max={2048} step={64} />
            <ParamInput label="Height" value={height} onChange={setHeight} min={64} max={2048} step={64} />
            <ParamInput label="Steps" value={steps} onChange={setSteps} min={1} max={100} step={1} />
            <ParamInput
              label="CFG Scale"
              value={cfgScale}
              onChange={setCfgScale}
              min={1}
              max={20}
              step={0.5}
              isFloat
            />
          </div>
        </div>

        {/* Generate button */}
        <div>
          <button
            onClick={handleGenerate}
            disabled={!prompt.trim() || generating}
            className="px-6 py-2.5 rounded-[10px] bg-accent text-white text-sm font-semibold hover:bg-accent-hover disabled:bg-border disabled:text-text-muted transition-colors cursor-pointer"
          >
            {generating ? 'Generating…' : 'Generate Image'}
          </button>
        </div>

        {/* Image display */}
        <div className="min-h-[400px] flex items-center justify-center rounded-xl border border-border bg-input-bg">
          {generating ? (
            <p className="text-sm text-text-muted animate-pulse">Generating image…</p>
          ) : error ? (
            <p className="text-sm text-danger">{error}</p>
          ) : imageUrl ? (
            <img
              src={imageUrl}
              alt="Generated"
              className="max-w-full max-h-[600px] rounded-lg object-contain"
            />
          ) : (
            <p className="text-sm text-text-muted">Generated image will appear here…</p>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Small helper component ───────────────────────────────────────────────

interface ParamInputProps {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step: number;
  isFloat?: boolean;
}

function ParamInput({ label, value, onChange, min, max, step, isFloat }: ParamInputProps) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-text-secondary">{label}</span>
      <input
        type="number"
        value={value}
        onChange={(e) => {
          const v = isFloat ? parseFloat(e.target.value) : parseInt(e.target.value, 10);
          if (!isNaN(v)) onChange(Math.min(max, Math.max(min, v)));
        }}
        min={min}
        max={max}
        step={step}
        className="w-20 bg-input-bg text-text-primary border border-border rounded-lg px-2.5 py-1.5 text-[13px] outline-none focus:border-border-light transition-colors"
      />
    </div>
  );
}
