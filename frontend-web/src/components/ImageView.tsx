import { useState, useEffect, useCallback, useRef, type ChangeEvent, type MouseEvent as ReactMouseEvent, type DragEvent as ReactDragEvent } from 'react';
import * as api from '../api/client';
import { useChat } from '../context/ChatContext';

// ── Types ─────────────────────────────────────────────────────────────────

interface GeneratedImage {
  url: string;
  filename: string;
}

interface GenerationMeta {
  prompt: string;
  negative_prompt?: string | null;
  model?: string | null;
  sampler?: string;
  steps?: number;
  cfg_scale?: number;
  seed?: number;
  width?: number;
  height?: number;
}

// ── Sub-components ────────────────────────────────────────────────────────

interface SliderInputProps {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step: number;
  disabled?: boolean;
}

function SliderInput({ label, value, onChange, min, max, step, disabled }: SliderInputProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-text-secondary tracking-wide">{label}</span>
        <input
          type="number"
          value={value}
          disabled={disabled}
          onChange={(e) => {
            const v = step < 1 ? parseFloat(e.target.value) : parseInt(e.target.value, 10);
            if (!isNaN(v)) onChange(Math.min(max, Math.max(min, v)));
          }}
          min={min}
          max={max}
          step={step}
          className="w-16 bg-input-bg text-text-primary border border-border rounded-lg px-2 py-1 text-xs outline-none focus:border-border-light transition-colors disabled:opacity-50 text-right"
        />
      </div>
      <input
        type="range"
        value={value}
        disabled={disabled}
        onChange={(e) => {
          const v = step < 1 ? parseFloat(e.target.value) : parseInt(e.target.value, 10);
          onChange(v);
        }}
        min={min}
        max={max}
        step={step}
        className="w-full h-1.5 appearance-none bg-border rounded-full outline-none cursor-pointer accent-accent disabled:opacity-50"
      />
    </div>
  );
}

interface SelectProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
  placeholder?: string;
  disabled?: boolean;
}

function Select({ label, value, onChange, options, placeholder, disabled }: SelectProps) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-xs font-semibold text-text-secondary tracking-wide">{label}</label>}
      <select
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2 text-sm outline-none focus:border-border-light transition-colors disabled:opacity-50 cursor-pointer"
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((opt) => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    </div>
  );
}

// ── Lightbox ──────────────────────────────────────────────────────────────

function Lightbox({ url, onClose }: { url: string; onClose: () => void }) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <img
        src={url}
        alt="Generated full size"
        className="max-w-[90vw] max-h-[90vh] object-contain rounded-xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      />
      <button
        onClick={onClose}
        className="absolute top-4 right-4 text-white/70 hover:text-white text-2xl font-light w-10 h-10 flex items-center justify-center rounded-full bg-black/40 hover:bg-black/60 transition-colors"
      >
        ✕
      </button>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────

export default function ImageView() {
  const { state, dispatch } = useChat();

  // ── Generation params ────────────────────────────────────────────────
  const [prompt, setPrompt] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [model, setModel] = useState('');
  const [sampler, setSampler] = useState('Euler a');
  const [steps, setSteps] = useState(20);
  const [cfgScale, setCfgScale] = useState(7.0);
  const [width, setWidth] = useState(512);
  const [height, setHeight] = useState(512);
  const [seed, setSeed] = useState(-1);
  const [batchSize, setBatchSize] = useState(1);
  const [batchCount, setBatchCount] = useState(1);
  const [restoreFaces, setRestoreFaces] = useState(false);
  const [tiling, setTiling] = useState(false);
  const [clipSkip, setClipSkip] = useState(1);
  const [selectedLoras, setSelectedLoras] = useState<string[]>([]);
  const [selectedStyles, setSelectedStyles] = useState<string[]>([]);

  // Hires fix
  const [enableHr, setEnableHr] = useState(false);
  const [hrScale, setHrScale] = useState(2.0);
  const [hrUpscaler, setHrUpscaler] = useState('');
  const [hrSteps, setHrSteps] = useState(0);
  const [denoisingStrength, setDenoisingStrength] = useState(0.7);
  const [hiresExpanded, setHiresExpanded] = useState(false);

  // ── Mode (txt2img / img2img / inpaint) ────────────────────────────────
  const [genMode, setGenMode] = useState<'txt2img' | 'img2img' | 'inpaint'>('txt2img');

  // ── img2img state ─────────────────────────────────────────────────────
  const [initImage, setInitImage] = useState<string | null>(null);       // base64 or /images/ URL
  const [initImagePreview, setInitImagePreview] = useState<string | null>(null); // data URL for preview
  const [img2imgDenoise, setImg2imgDenoise] = useState(0.75);
  const [resizeMode, setResizeMode] = useState(0);
  const [showSessionImages, setShowSessionImages] = useState(false);
  const initImageFileRef = useRef<HTMLInputElement>(null);

  // ── Inpainting state ──────────────────────────────────────────────────
  const [maskBrushSize, setMaskBrushSize] = useState(20);
  const [maskBlur, setMaskBlur] = useState(4);
  const [inpaintingFill, setInpaintingFill] = useState(1);
  const [inpaintFullRes, setInpaintFullRes] = useState(true);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const isDrawingRef = useRef(false);

  // ── Option lists ─────────────────────────────────────────────────────
  const [imageModels, setImageModels] = useState<string[]>([]);
  const [loras, setLoras] = useState<string[]>([]);
  const [samplers, setSamplers] = useState<string[]>([]);
  const [upscalers, setUpscalers] = useState<string[]>([]);
  const [styles, setStyles] = useState<string[]>([]);
  const [loadingOptions, setLoadingOptions] = useState(true);

  // ── LoRA search ──────────────────────────────────────────────────────
  const [loraSearch, setLoraSearch] = useState('');
  const [loraDropdownOpen, setLoraDropdownOpen] = useState(false);
  const loraRef = useRef<HTMLDivElement>(null);

  // ── Refresh checkpoints state ────────────────────────────────────────
  const [refreshingCheckpoints, setRefreshingCheckpoints] = useState(false);

  // ── Output state ─────────────────────────────────────────────────────
  const [generating, setGenerating] = useState(false);
  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([]);
  const [lastMeta, setLastMeta] = useState<GenerationMeta | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lightboxUrl, setLightboxUrl] = useState<string | null>(null);

  // ── Fetch all options on mount ───────────────────────────────────────

  const fetchOptions = useCallback(async () => {
    setLoadingOptions(true);
    try {
      const [modelsData, samplersData, upscalersData, stylesData] = await Promise.allSettled([
        api.listModels(),
        api.auto1111Samplers(),
        api.auto1111Upscalers(),
        api.auto1111Styles(),
      ]);

      if (modelsData.status === 'fulfilled') {
        setImageModels(modelsData.value.image ?? []);
        setLoras(modelsData.value.loras ?? []);
        if (modelsData.value.image.length > 0) setModel(modelsData.value.image[0]);
      }
      if (samplersData.status === 'fulfilled') {
        const s = samplersData.value.samplers ?? [];
        setSamplers(s);
        if (s.includes('Euler a')) setSampler('Euler a');
        else if (s.length > 0) setSampler(s[0]);
      }
      if (upscalersData.status === 'fulfilled') {
        const u = upscalersData.value.upscalers ?? [];
        setUpscalers(u);
        if (u.length > 0) setHrUpscaler(u[0]);
      }
      if (stylesData.status === 'fulfilled') {
        setStyles(stylesData.value.styles ?? []);
      }
    } finally {
      setLoadingOptions(false);
    }
  }, []);

  useEffect(() => {
    fetchOptions();
  }, [fetchOptions]);

  // ── Refresh checkpoints handler ───────────────────────────────────────

  const handleRefreshCheckpoints = useCallback(async () => {
    setRefreshingCheckpoints(true);
    try {
      await api.refreshCheckpoints();
      await fetchOptions();
    } catch {
      // ignore errors
    } finally {
      setRefreshingCheckpoints(false);
    }
  }, [fetchOptions]);

  // ── Apply image template from gallery ────────────────────────────────

  useEffect(() => {
    const tmpl = state.imageTemplate;
    if (!tmpl) return;
    if (typeof tmpl.prompt === 'string') setPrompt(tmpl.prompt);
    if (typeof tmpl.negative_prompt === 'string') setNegativePrompt(tmpl.negative_prompt);
    if (typeof tmpl.model === 'string') setModel(tmpl.model);
    if (typeof tmpl.sampler === 'string') setSampler(tmpl.sampler);
    if (typeof tmpl.steps === 'number') setSteps(tmpl.steps);
    if (typeof tmpl.cfg_scale === 'number') setCfgScale(tmpl.cfg_scale);
    if (typeof tmpl.seed === 'number') setSeed(tmpl.seed);
    if (typeof tmpl.width === 'number') setWidth(tmpl.width);
    if (typeof tmpl.height === 'number') setHeight(tmpl.height);
    if (Array.isArray(tmpl.lora)) setSelectedLoras(tmpl.lora as string[]);
    // Clear template after applying
    dispatch({ type: 'SET_IMAGE_TEMPLATE', template: null });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Close LoRA dropdown on outside click ─────────────────────────────

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (loraRef.current && !loraRef.current.contains(e.target as Node)) {
        setLoraDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  // ── img2img helpers ───────────────────────────────────────────────────

  const handleInitImageFile = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      setInitImagePreview(dataUrl);
      // Extract pure base64 (strip data:...;base64, prefix)
      const b64 = dataUrl.split(',')[1];
      setInitImage(b64);
    };
    reader.readAsDataURL(file);
  }, []);

  const handleInitImageDrop = useCallback((e: ReactDragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file || !file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      setInitImagePreview(dataUrl);
      setInitImage(dataUrl.split(',')[1]);
    };
    reader.readAsDataURL(file);
  }, []);

  // ── Canvas (inpaint) helpers ──────────────────────────────────────────

  const startDrawing = useCallback((e: ReactMouseEvent<HTMLCanvasElement>) => {
    isDrawingRef.current = true;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.beginPath();
    ctx.arc(x, y, maskBrushSize / 2, 0, Math.PI * 2);
    ctx.fillStyle = 'white';
    ctx.fill();
  }, [maskBrushSize]);

  const continueDrawing = useCallback((e: ReactMouseEvent<HTMLCanvasElement>) => {
    if (!isDrawingRef.current) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.beginPath();
    ctx.arc(x, y, maskBrushSize / 2, 0, Math.PI * 2);
    ctx.fillStyle = 'white';
    ctx.fill();
  }, [maskBrushSize]);

  const stopDrawing = useCallback(() => {
    isDrawingRef.current = false;
  }, []);

  const clearMask = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }, []);

  const invertMask = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < imageData.data.length; i += 4) {
      const alpha = imageData.data[i + 3];
      // White pixels (alpha > 0) → transparent; transparent → white
      if (alpha > 0) {
        imageData.data[i] = 0;
        imageData.data[i + 1] = 0;
        imageData.data[i + 2] = 0;
        imageData.data[i + 3] = 0;
      } else {
        imageData.data[i] = 255;
        imageData.data[i + 1] = 255;
        imageData.data[i + 2] = 255;
        imageData.data[i + 3] = 255;
      }
    }
    ctx.putImageData(imageData, 0, 0);
  }, []);

  // ── Generate ─────────────────────────────────────────────────────────

  const handleGenerate = async () => {
    if (!prompt.trim() || generating) return;

    // For img2img/inpaint, init_image is required
    if ((genMode === 'img2img' || genMode === 'inpaint') && !initImage) {
      setError('Please provide an input image.');
      return;
    }

    setGenerating(true);
    setError(null);

    try {
      let res: api.ImageGenerateResponse | api.Img2ImgResponse;

      if (genMode === 'txt2img') {
        const req: api.ImageGenerateRequest = {
          prompt: prompt.trim(),
          negative_prompt: negativePrompt.trim() || undefined,
          model: model || undefined,
          sampler,
          steps,
          cfg_scale: cfgScale,
          width,
          height,
          seed,
          batch_size: batchSize,
          batch_count: batchCount,
          restore_faces: restoreFaces,
          tiling,
          clip_skip: clipSkip,
          lora: selectedLoras.length > 0 ? selectedLoras : undefined,
          styles: selectedStyles.length > 0 ? selectedStyles : undefined,
          enable_hr: enableHr,
          hr_scale: hrScale,
          hr_upscaler: hrUpscaler || undefined,
          hr_second_pass_steps: hrSteps,
          denoising_strength: denoisingStrength,
        };
        res = await api.generateImage(req);
      } else {
        // img2img or inpaint
        let maskB64: string | undefined;
        if (genMode === 'inpaint' && canvasRef.current) {
          maskB64 = canvasRef.current.toDataURL('image/png').split(',')[1];
        }

        const req: api.Img2ImgRequest = {
          prompt: prompt.trim(),
          negative_prompt: negativePrompt.trim() || undefined,
          model: model || undefined,
          sampler,
          steps,
          cfg_scale: cfgScale,
          width,
          height,
          seed,
          batch_size: batchSize,
          restore_faces: restoreFaces,
          tiling,
          clip_skip: clipSkip,
          lora: selectedLoras.length > 0 ? selectedLoras : undefined,
          styles: selectedStyles.length > 0 ? selectedStyles : undefined,
          init_image: initImage!,
          denoising_strength: img2imgDenoise,
          resize_mode: resizeMode,
          ...(genMode === 'inpaint' && maskB64
            ? {
                mask: maskB64,
                mask_blur: maskBlur,
                inpainting_fill: inpaintingFill,
                inpaint_full_res: inpaintFullRes,
              }
            : {}),
        };
        res = await api.img2img(req);
      }

      const imgs: GeneratedImage[] = (res.images && res.images.length > 0)
        ? res.images.map((url) => ({ url, filename: url.split('/').pop() ?? url }))
        : [{ url: res.image_url ?? res.image_path, filename: res.filename }];

      setGeneratedImages(imgs);
      setLastMeta({
        prompt: prompt.trim(),
        negative_prompt: negativePrompt.trim() || null,
        model: model || null,
        sampler,
        steps,
        cfg_scale: cfgScale,
        seed: (res.metadata?.seed as number) ?? seed,
        width,
        height,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Image generation failed');
    } finally {
      setGenerating(false);
    }
  };

  // ── LoRA helpers ─────────────────────────────────────────────────────

  const filteredLoras = loras.filter(
    (l) => l.toLowerCase().includes(loraSearch.toLowerCase()) && !selectedLoras.includes(l)
  );

  const toggleLora = (lora: string) => {
    setSelectedLoras((prev) =>
      prev.includes(lora) ? prev.filter((l) => l !== lora) : [...prev, lora]
    );
  };

  const toggleStyle = (style: string) => {
    setSelectedStyles((prev) =>
      prev.includes(style) ? prev.filter((s) => s !== style) : [...prev, style]
    );
  };

  // ── Preset buttons ───────────────────────────────────────────────────

  const sizePresets = [
    { label: '512²', w: 512, h: 512 },
    { label: '768²', w: 768, h: 768 },
    { label: '512×768', w: 512, h: 768 },
    { label: '768×512', w: 768, h: 512 },
    { label: '1024²', w: 1024, h: 1024 },
  ];

  // ── Render ───────────────────────────────────────────────────────────

  return (
    <div className="flex-1 overflow-hidden flex flex-col">
      <div className="flex-1 overflow-hidden flex flex-col lg:flex-row">

        {/* ── Left: Controls ─────────────────────────────────────────── */}
        <div className="lg:w-[40%] overflow-y-auto border-b lg:border-b-0 lg:border-r border-border flex-shrink-0">
          <div className="px-3 sm:px-5 py-4 sm:py-5 flex flex-col gap-4">

            {/* Header */}
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-text-primary">Image Generation</h2>
              {loadingOptions && (
                <span className="text-xs text-text-muted animate-pulse">Loading options…</span>
              )}
            </div>

            {/* Mode tabs */}
            <div className="flex rounded-xl overflow-hidden border border-border">
              {(['txt2img', 'img2img', 'inpaint'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setGenMode(mode)}
                  disabled={generating}
                  className={`flex-1 py-2 text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50 ${
                    genMode === mode
                      ? 'bg-button-active text-text-primary'
                      : 'text-text-secondary hover:bg-button-hover'
                  }`}
                >
                  {mode === 'txt2img' ? 'txt2img' : mode === 'img2img' ? 'img2img' : 'Inpainting'}
                </button>
              ))}
            </div>

            {/* Checkpoint */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-text-secondary tracking-wide">Checkpoint</label>
                <button
                  onClick={handleRefreshCheckpoints}
                  disabled={generating || refreshingCheckpoints}
                  title="Refresh checkpoints"
                  className="text-xs text-accent hover:text-accent/80 disabled:opacity-50 transition-colors cursor-pointer flex items-center gap-1"
                >
                  {refreshingCheckpoints ? (
                    <span className="w-3 h-3 border border-accent/30 border-t-accent rounded-full animate-spin inline-block" />
                  ) : '↻'} Refresh
                </button>
              </div>
              {imageModels.length === 0 && !loadingOptions ? (
                <div className="rounded-xl border border-border bg-input-bg px-3 py-3 text-xs text-text-muted">
                  No checkpoints found. Make sure Automatic1111 is running and has model files in its models directory. Click Refresh to scan.
                </div>
              ) : (
                <Select
                  label=""
                  value={model}
                  onChange={setModel}
                  options={imageModels}
                  placeholder={imageModels.length === 0 ? 'No models found' : undefined}
                  disabled={generating}
                />
              )}
            </div>

            {/* Input image (img2img / inpaint) */}
            {(genMode === 'img2img' || genMode === 'inpaint') && (
              <div className="flex flex-col gap-2">
                <label className="text-xs font-semibold text-text-secondary tracking-wide">Input Image</label>

                {/* Drop zone */}
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleInitImageDrop}
                  onClick={() => !initImage && initImageFileRef.current?.click()}
                  className={`relative border-2 border-dashed rounded-xl flex flex-col items-center justify-center transition-colors ${
                    initImage
                      ? 'border-accent/40 p-1'
                      : 'border-border hover:border-border-light cursor-pointer py-6 gap-2'
                  }`}
                >
                  {initImage && initImagePreview ? (
                    <div className="relative w-full">
                      <img
                        src={initImagePreview}
                        alt="Input"
                        className="w-full h-32 object-cover rounded-lg"
                      />
                      <button
                        onClick={(e) => { e.stopPropagation(); setInitImage(null); setInitImagePreview(null); clearMask(); }}
                        className="absolute top-1 right-1 w-6 h-6 bg-black/60 hover:bg-black/80 text-white rounded-full text-xs flex items-center justify-center cursor-pointer"
                      >
                        ✕
                      </button>
                    </div>
                  ) : (
                    <>
                      <span className="text-text-muted text-sm">Drop image here or click to browse</span>
                      <span className="text-text-muted text-xs opacity-60">PNG, JPG, WebP…</span>
                    </>
                  )}
                </div>

                <input
                  ref={initImageFileRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleInitImageFile}
                />

                {/* Use generated image picker */}
                {generatedImages.length > 0 && (
                  <div className="relative">
                    <button
                      onClick={() => setShowSessionImages((v) => !v)}
                      className="text-xs text-accent hover:text-accent/80 transition-colors cursor-pointer"
                    >
                      Use generated image ▾
                    </button>
                    {showSessionImages && (
                      <div className="absolute z-20 mt-1 bg-sidebar-bg border border-border rounded-xl shadow-xl overflow-hidden w-full">
                        <div className="flex gap-1.5 p-2 overflow-x-auto">
                          {generatedImages.slice(-5).map((img, i) => (
                            <button
                              key={i}
                              onClick={() => {
                                setInitImage(img.url);
                                setInitImagePreview(img.url);
                                setShowSessionImages(false);
                                clearMask();
                              }}
                              className="flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden border border-border hover:border-accent transition-colors cursor-pointer"
                            >
                              <img src={img.url} alt="" className="w-full h-full object-cover" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Prompt */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-secondary tracking-wide">Prompt</label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe the image you want to generate…"
                rows={3}
                disabled={generating}
                className="w-full bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2.5 text-sm outline-none focus:border-border-light resize-none transition-colors placeholder:text-text-muted disabled:opacity-60"
              />
            </div>

            {/* Negative Prompt */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-secondary tracking-wide">Negative Prompt</label>
              <textarea
                value={negativePrompt}
                onChange={(e) => setNegativePrompt(e.target.value)}
                placeholder="Things to avoid (optional)…"
                rows={2}
                disabled={generating}
                className="w-full bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2.5 text-sm outline-none focus:border-border-light resize-none transition-colors placeholder:text-text-muted disabled:opacity-60"
              />
            </div>

            {/* Sampler */}
            <Select
              label="Sampler"
              value={sampler}
              onChange={setSampler}
              options={samplers.length > 0 ? samplers : ['Euler a', 'Euler', 'DPM++ 2M Karras', 'DPM++ SDE Karras', 'DDIM']}
              disabled={generating}
            />

            {/* Steps */}
            <SliderInput label="Steps" value={steps} onChange={setSteps} min={1} max={100} step={1} disabled={generating} />

            {/* CFG Scale */}
            <SliderInput label="CFG Scale" value={cfgScale} onChange={setCfgScale} min={1} max={20} step={0.5} disabled={generating} />

            {/* Width × Height */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-secondary tracking-wide">Size</label>
              <div className="flex gap-2 items-center">
                <div className="flex flex-col gap-1 flex-1">
                  <span className="text-[11px] text-text-muted">Width</span>
                  <input
                    type="number"
                    value={width}
                    disabled={generating}
                    onChange={(e) => { const v = parseInt(e.target.value, 10); if (!isNaN(v)) setWidth(Math.min(2048, Math.max(64, v))); }}
                    min={64} max={2048} step={64}
                    className="w-full bg-input-bg text-text-primary border border-border rounded-lg px-2.5 py-1.5 text-sm outline-none focus:border-border-light transition-colors disabled:opacity-50"
                  />
                </div>
                <span className="text-text-muted mt-4">×</span>
                <div className="flex flex-col gap-1 flex-1">
                  <span className="text-[11px] text-text-muted">Height</span>
                  <input
                    type="number"
                    value={height}
                    disabled={generating}
                    onChange={(e) => { const v = parseInt(e.target.value, 10); if (!isNaN(v)) setHeight(Math.min(2048, Math.max(64, v))); }}
                    min={64} max={2048} step={64}
                    className="w-full bg-input-bg text-text-primary border border-border rounded-lg px-2.5 py-1.5 text-sm outline-none focus:border-border-light transition-colors disabled:opacity-50"
                  />
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5 mt-0.5">
                {sizePresets.map((p) => (
                  <button
                    key={p.label}
                    onClick={() => { setWidth(p.w); setHeight(p.h); }}
                    disabled={generating}
                    className="text-[11px] px-2 py-0.5 rounded-md bg-input-bg border border-border text-text-secondary hover:border-border-light hover:text-text-primary transition-colors disabled:opacity-40 cursor-pointer"
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Seed */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-secondary tracking-wide">Seed</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={seed === -1 ? '' : seed}
                  placeholder="Random"
                  disabled={generating}
                  onChange={(e) => {
                    const raw = e.target.value;
                    if (raw === '' || raw === '-') { setSeed(-1); return; }
                    const v = parseInt(raw, 10);
                    if (!isNaN(v)) setSeed(v);
                  }}
                  className="flex-1 bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2 text-sm outline-none focus:border-border-light transition-colors placeholder:text-text-muted disabled:opacity-50"
                />
                <button
                  onClick={() => setSeed(-1)}
                  disabled={generating}
                  title="Random seed"
                  className="px-3 py-2 rounded-xl bg-input-bg border border-border text-text-secondary hover:border-border-light hover:text-text-primary transition-colors disabled:opacity-40 cursor-pointer text-base"
                >
                  🎲
                </button>
              </div>
            </div>

            {/* Batch */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-secondary tracking-wide">Batch</label>
              <div className="flex gap-3">
                <div className="flex flex-col gap-1 flex-1">
                  <span className="text-[11px] text-text-muted">Images per batch</span>
                  <input
                    type="number"
                    value={batchSize}
                    disabled={generating}
                    onChange={(e) => { const v = parseInt(e.target.value, 10); if (!isNaN(v)) setBatchSize(Math.min(8, Math.max(1, v))); }}
                    min={1} max={8}
                    className="w-full bg-input-bg text-text-primary border border-border rounded-lg px-2.5 py-1.5 text-sm outline-none focus:border-border-light transition-colors disabled:opacity-50"
                  />
                </div>
                <div className="flex flex-col gap-1 flex-1">
                  <span className="text-[11px] text-text-muted">Batches</span>
                  <input
                    type="number"
                    value={batchCount}
                    disabled={generating}
                    onChange={(e) => { const v = parseInt(e.target.value, 10); if (!isNaN(v)) setBatchCount(Math.min(8, Math.max(1, v))); }}
                    min={1} max={8}
                    className="w-full bg-input-bg text-text-primary border border-border rounded-lg px-2.5 py-1.5 text-sm outline-none focus:border-border-light transition-colors disabled:opacity-50"
                  />
                </div>
              </div>
            </div>

            {/* Sampling options */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-secondary tracking-wide">Options</label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={restoreFaces}
                    disabled={generating}
                    onChange={(e) => setRestoreFaces(e.target.checked)}
                    className="accent-accent w-3.5 h-3.5"
                  />
                  <span className="text-sm text-text-primary">Restore Faces</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={tiling}
                    disabled={generating}
                    onChange={(e) => setTiling(e.target.checked)}
                    className="accent-accent w-3.5 h-3.5"
                  />
                  <span className="text-sm text-text-primary">Tiling</span>
                </label>
              </div>
            </div>

            {/* LoRA multi-select */}
            <div className="flex flex-col gap-1.5" ref={loraRef}>
              <label className="text-xs font-semibold text-text-secondary tracking-wide">LoRA</label>
              {selectedLoras.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {selectedLoras.map((l) => (
                    <span
                      key={l}
                      className="inline-flex items-center gap-1 text-xs bg-accent/20 text-accent border border-accent/30 rounded-full px-2.5 py-0.5"
                    >
                      {l}
                      <button
                        onClick={() => toggleLora(l)}
                        className="ml-0.5 hover:text-white transition-colors cursor-pointer"
                      >
                        ✕
                      </button>
                    </span>
                  ))}
                </div>
              )}
              <div className="relative">
                <input
                  type="text"
                  value={loraSearch}
                  onFocus={() => setLoraDropdownOpen(true)}
                  onChange={(e) => { setLoraSearch(e.target.value); setLoraDropdownOpen(true); }}
                  placeholder={loras.length === 0 ? 'No LoRAs available' : 'Search LoRAs…'}
                  disabled={generating || loras.length === 0}
                  className="w-full bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2 text-sm outline-none focus:border-border-light transition-colors placeholder:text-text-muted disabled:opacity-50"
                />
                {loraDropdownOpen && filteredLoras.length > 0 && (
                  <div className="absolute z-20 mt-1 w-full bg-sidebar-bg border border-border rounded-xl shadow-xl overflow-hidden">
                    <div className="max-h-44 overflow-y-auto">
                      {filteredLoras.slice(0, 50).map((l) => (
                        <button
                          key={l}
                          onMouseDown={(e) => { e.preventDefault(); toggleLora(l); setLoraSearch(''); }}
                          className="w-full text-left px-3 py-1.5 text-sm text-text-primary hover:bg-button-hover transition-colors cursor-pointer"
                        >
                          {l}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Styles */}
            {styles.length > 0 && (
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-text-secondary tracking-wide">Styles</label>
                <div className="flex flex-wrap gap-1.5">
                  {styles.map((s) => (
                    <button
                      key={s}
                      onClick={() => toggleStyle(s)}
                      disabled={generating}
                      className={`text-xs px-2.5 py-1 rounded-full border transition-colors cursor-pointer disabled:opacity-40 ${
                        selectedStyles.includes(s)
                          ? 'bg-accent/20 text-accent border-accent/40'
                          : 'bg-input-bg text-text-secondary border-border hover:border-border-light hover:text-text-primary'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Clip Skip */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-secondary tracking-wide">Clip Skip</label>
              <input
                type="number"
                value={clipSkip}
                disabled={generating}
                onChange={(e) => { const v = parseInt(e.target.value, 10); if (!isNaN(v)) setClipSkip(Math.min(12, Math.max(1, v))); }}
                min={1} max={12}
                className="w-20 bg-input-bg text-text-primary border border-border rounded-lg px-2.5 py-1.5 text-sm outline-none focus:border-border-light transition-colors disabled:opacity-50"
              />
            </div>

            {/* Hires Fix (txt2img only) */}
            {genMode === 'txt2img' && <div className="flex flex-col gap-0 border border-border rounded-xl overflow-hidden">
              <button
                onClick={() => setHiresExpanded((v) => !v)}
                disabled={generating}
                className="flex items-center justify-between px-3 py-2.5 text-sm font-semibold text-text-primary hover:bg-button-hover transition-colors cursor-pointer disabled:opacity-50 w-full text-left"
              >
                <span className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={enableHr}
                    disabled={generating}
                    onClick={(e) => e.stopPropagation()}
                    onChange={(e) => { setEnableHr(e.target.checked); if (e.target.checked) setHiresExpanded(true); }}
                    className="accent-accent w-3.5 h-3.5"
                  />
                  Hires Fix
                </span>
                <span className="text-text-muted text-xs">{hiresExpanded ? '▲' : '▼'}</span>
              </button>

              {hiresExpanded && (
                <div className="px-3 pb-3 pt-2 flex flex-col gap-3 border-t border-border bg-input-bg/30">
                  <Select
                    label="Upscaler"
                    value={hrUpscaler}
                    onChange={setHrUpscaler}
                    options={upscalers.length > 0 ? upscalers : ['Latent', 'ESRGAN_4x', 'R-ESRGAN 4x+']}
                    disabled={generating || !enableHr}
                  />
                  <SliderInput label="Upscale by" value={hrScale} onChange={setHrScale} min={1.0} max={4.0} step={0.05} disabled={generating || !enableHr} />
                  <SliderInput label="Hires steps" value={hrSteps} onChange={setHrSteps} min={0} max={100} step={1} disabled={generating || !enableHr} />
                  <SliderInput label="Denoising strength" value={denoisingStrength} onChange={setDenoisingStrength} min={0.0} max={1.0} step={0.01} disabled={generating || !enableHr} />
                </div>
              )}
            </div>}

            {/* img2img specific controls */}
            {(genMode === 'img2img' || genMode === 'inpaint') && (
              <>
                <SliderInput
                  label="Denoising Strength"
                  value={img2imgDenoise}
                  onChange={setImg2imgDenoise}
                  min={0.0}
                  max={1.0}
                  step={0.01}
                  disabled={generating}
                />
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-text-secondary tracking-wide">Resize Mode</label>
                  <select
                    value={resizeMode}
                    disabled={generating}
                    onChange={(e) => setResizeMode(parseInt(e.target.value, 10))}
                    className="w-full bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2 text-sm outline-none focus:border-border-light transition-colors disabled:opacity-50 cursor-pointer"
                  >
                    <option value={0}>Just resize</option>
                    <option value={1}>Crop and resize</option>
                    <option value={2}>Resize and fill</option>
                  </select>
                </div>
              </>
            )}

            {/* Inpainting canvas */}
            {genMode === 'inpaint' && initImage && (
              <div className="flex flex-col gap-2">
                <label className="text-xs font-semibold text-text-secondary tracking-wide">Mask Editor</label>
                <div className="relative rounded-xl overflow-hidden border border-border bg-input-bg" style={{ aspectRatio: '1 / 1' }}>
                  {/* Background image */}
                  {initImagePreview && (
                    <img
                      src={initImagePreview}
                      alt="Base"
                      className="absolute inset-0 w-full h-full object-cover"
                      draggable={false}
                    />
                  )}
                  {/* Mask canvas */}
                  <canvas
                    ref={canvasRef}
                    width={512}
                    height={512}
                    className="absolute inset-0 w-full h-full opacity-60 cursor-crosshair"
                    style={{ touchAction: 'none' }}
                    onMouseDown={startDrawing}
                    onMouseMove={continueDrawing}
                    onMouseUp={stopDrawing}
                    onMouseLeave={stopDrawing}
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={clearMask}
                    disabled={generating}
                    className="flex-1 py-1.5 text-xs border border-border rounded-lg text-text-secondary hover:bg-button-hover transition-colors cursor-pointer disabled:opacity-40"
                  >
                    Clear mask
                  </button>
                  <button
                    onClick={invertMask}
                    disabled={generating}
                    className="flex-1 py-1.5 text-xs border border-border rounded-lg text-text-secondary hover:bg-button-hover transition-colors cursor-pointer disabled:opacity-40"
                  >
                    Invert mask
                  </button>
                </div>
                <SliderInput
                  label="Brush size"
                  value={maskBrushSize}
                  onChange={setMaskBrushSize}
                  min={4}
                  max={60}
                  step={1}
                  disabled={generating}
                />
                <SliderInput
                  label="Mask Blur"
                  value={maskBlur}
                  onChange={setMaskBlur}
                  min={0}
                  max={16}
                  step={1}
                  disabled={generating}
                />
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-text-secondary tracking-wide">Inpainting Fill</label>
                  <select
                    value={inpaintingFill}
                    disabled={generating}
                    onChange={(e) => setInpaintingFill(parseInt(e.target.value, 10))}
                    className="w-full bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2 text-sm outline-none focus:border-border-light transition-colors disabled:opacity-50 cursor-pointer"
                  >
                    <option value={0}>Fill</option>
                    <option value={1}>Original</option>
                    <option value={2}>Latent noise</option>
                    <option value={3}>Latent nothing</option>
                  </select>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={inpaintFullRes}
                    disabled={generating}
                    onChange={(e) => setInpaintFullRes(e.target.checked)}
                    className="accent-accent w-3.5 h-3.5"
                  />
                  <span className="text-sm text-text-primary">Full resolution inpainting</span>
                </label>
              </div>
            )}

            {/* Generate */}
            <button
              onClick={handleGenerate}
              disabled={!prompt.trim() || generating || ((genMode === 'img2img' || genMode === 'inpaint') && !initImage)}
              className="w-full py-3 rounded-xl bg-accent text-white text-sm font-semibold hover:bg-accent-hover disabled:bg-border disabled:text-text-muted transition-colors cursor-pointer"
            >
              {generating ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Generating…
                </span>
              ) : genMode === 'txt2img' ? 'Generate Image' : genMode === 'img2img' ? 'Generate (img2img)' : 'Generate (Inpaint)'}
            </button>

          </div>
        </div>

        {/* ── Right: Output ───────────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-3 sm:px-5 py-4 sm:py-5 flex flex-col gap-4">

            {/* Error */}
            {error && (
              <div className="rounded-xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
                {error}
              </div>
            )}

            {/* Progress */}
            {generating && (
              <div className="rounded-xl border border-border bg-input-bg flex flex-col items-center justify-center py-16 gap-3">
                <div className="w-8 h-8 border-2 border-border border-t-accent rounded-full animate-spin" />
                <p className="text-sm text-text-muted animate-pulse">Generating…</p>
              </div>
            )}

            {/* Image gallery */}
            {!generating && generatedImages.length > 0 && (
              <>
                <div
                  className={`grid gap-3 ${
                    generatedImages.length === 1
                      ? 'grid-cols-1'
                      : generatedImages.length <= 4
                      ? 'grid-cols-2'
                      : 'grid-cols-3'
                  }`}
                >
                  {generatedImages.map((img, i) => (
                    <div key={i} className="relative group rounded-xl overflow-hidden border border-border bg-input-bg aspect-square">
                      <img
                        src={img.url}
                        alt={`Generated ${i + 1}`}
                        className="w-full h-full object-cover cursor-pointer transition-transform group-hover:scale-[1.02]"
                        onClick={() => setLightboxUrl(img.url)}
                      />
                      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors pointer-events-none" />
                      <div className="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setInitImage(img.url);
                            setInitImagePreview(img.url);
                            setGenMode('img2img');
                            clearMask();
                          }}
                          className="bg-black/60 hover:bg-black/80 text-white text-xs px-2 py-1 rounded-lg"
                          title="Send to img2img"
                        >
                          &#8594; img2img
                        </button>
                        <a
                          href={img.url}
                          download={img.filename}
                          onClick={(e) => e.stopPropagation()}
                          className="bg-black/60 hover:bg-black/80 text-white text-xs px-2 py-1 rounded-lg"
                        >
                          Download
                        </a>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Metadata */}
                {lastMeta && (
                  <div className="rounded-xl border border-border bg-input-bg px-4 py-3 flex flex-col gap-1.5">
                    <span className="text-xs font-semibold text-text-secondary tracking-wide mb-0.5">Generation Info</span>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                      {lastMeta.model && (
                        <MetaRow label="Model" value={lastMeta.model} />
                      )}
                      {lastMeta.sampler && (
                        <MetaRow label="Sampler" value={lastMeta.sampler} />
                      )}
                      {lastMeta.steps !== undefined && (
                        <MetaRow label="Steps" value={String(lastMeta.steps)} />
                      )}
                      {lastMeta.cfg_scale !== undefined && (
                        <MetaRow label="CFG" value={String(lastMeta.cfg_scale)} />
                      )}
                      {lastMeta.seed !== undefined && (
                        <MetaRow label="Seed" value={String(lastMeta.seed)} />
                      )}
                      {lastMeta.width && lastMeta.height && (
                        <MetaRow label="Size" value={`${lastMeta.width}×${lastMeta.height}`} />
                      )}
                    </div>
                    <div className="mt-1.5">
                      <span className="text-[11px] text-text-muted">Prompt: </span>
                      <span className="text-[11px] text-text-secondary break-words">{lastMeta.prompt}</span>
                    </div>
                    {lastMeta.negative_prompt && (
                      <div>
                        <span className="text-[11px] text-text-muted">Negative: </span>
                        <span className="text-[11px] text-text-secondary break-words">{lastMeta.negative_prompt}</span>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}

            {/* Empty state */}
            {!generating && generatedImages.length === 0 && !error && (
              <div className="rounded-xl border border-border bg-input-bg flex items-center justify-center py-24">
                <p className="text-sm text-text-muted">Generated images will appear here…</p>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Lightbox */}
      {lightboxUrl && (
        <Lightbox url={lightboxUrl} onClose={() => setLightboxUrl(null)} />
      )}
    </div>
  );
}

// ── Small helpers ─────────────────────────────────────────────────────────

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-1.5">
      <span className="text-[11px] text-text-muted shrink-0">{label}:</span>
      <span className="text-[11px] text-text-secondary truncate">{value}</span>
    </div>
  );
}
