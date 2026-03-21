import { useState, useEffect, useCallback } from 'react';
import * as api from '../api/client';
import { useChat } from '../context/ChatContext';

// ── Detail Modal ──────────────────────────────────────────────────────────

interface DetailModalProps {
  image: api.ImageRecord;
  onClose: () => void;
  onDelete: (id: number) => void;
  onUseAsTemplate: (image: api.ImageRecord) => void;
}

function DetailModal({ image, onClose, onDelete, onUseAsTemplate }: DetailModalProps) {
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  const imageUrl = `/images/${image.filename}`;
  const params = image.parameters as Record<string, unknown>;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-4xl max-h-[92vh] bg-sidebar-bg border border-border rounded-2xl shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-10 w-8 h-8 flex items-center justify-center rounded-lg text-text-secondary hover:bg-button-hover hover:text-text-primary transition-colors cursor-pointer"
        >
          ✕
        </button>

        <div className="flex flex-col lg:flex-row flex-1 overflow-hidden">
          {/* Image */}
          <div className="lg:w-[55%] flex items-center justify-center bg-black/30 p-4 shrink-0">
            <img
              src={imageUrl}
              alt={image.prompt}
              className="max-w-full max-h-[60vh] lg:max-h-[80vh] object-contain rounded-xl"
            />
          </div>

          {/* Metadata */}
          <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-4">
            <div>
              <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wide">Prompt</span>
              <p className="text-sm text-text-primary mt-1 break-words">{image.prompt}</p>
            </div>

            {image.negative_prompt && (
              <div>
                <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wide">Negative Prompt</span>
                <p className="text-sm text-text-secondary mt-1 break-words">{image.negative_prompt}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-x-4 gap-y-2">
              {image.model_name && <MetaCell label="Model" value={image.model_name} />}
              {params.sampler && <MetaCell label="Sampler" value={String(params.sampler)} />}
              {params.steps !== undefined && <MetaCell label="Steps" value={String(params.steps)} />}
              {params.cfg_scale !== undefined && <MetaCell label="CFG" value={String(params.cfg_scale)} />}
              {params.seed !== undefined && <MetaCell label="Seed" value={String(params.seed)} />}
              {image.width && image.height && (
                <MetaCell label="Size" value={`${image.width}×${image.height}`} />
              )}
            </div>

            {image.lora_used && image.lora_used.length > 0 && (
              <div>
                <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wide">LoRAs</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {image.lora_used.map((l) => (
                    <span key={l} className="text-xs bg-accent/10 text-accent border border-accent/20 rounded-full px-2 py-0.5">{l}</span>
                  ))}
                </div>
              </div>
            )}

            <div>
              <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wide">Date</span>
              <p className="text-xs text-text-secondary mt-1">{new Date(image.created_at).toLocaleString()}</p>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap gap-2 mt-auto pt-2">
              <a
                href={imageUrl}
                download={image.filename}
                className="px-4 py-2 rounded-xl bg-input-bg border border-border text-text-secondary text-sm hover:border-border-light hover:text-text-primary transition-colors cursor-pointer"
              >
                Download
              </a>
              <button
                onClick={() => { onUseAsTemplate(image); onClose(); }}
                className="px-4 py-2 rounded-xl bg-accent text-white text-sm font-medium hover:bg-accent-hover transition-colors cursor-pointer"
              >
                Use as Template
              </button>
              {confirmDelete ? (
                <>
                  <button
                    onClick={() => { onDelete(image.id); onClose(); }}
                    className="px-4 py-2 rounded-xl bg-danger/20 border border-danger/40 text-danger text-sm hover:bg-danger/30 transition-colors cursor-pointer"
                  >
                    Confirm Delete
                  </button>
                  <button
                    onClick={() => setConfirmDelete(false)}
                    className="px-4 py-2 rounded-xl border border-border text-text-secondary text-sm hover:bg-button-hover transition-colors cursor-pointer"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setConfirmDelete(true)}
                  className="px-4 py-2 rounded-xl border border-border text-text-muted text-sm hover:border-danger hover:text-danger transition-colors cursor-pointer"
                >
                  Delete
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetaCell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-[11px] text-text-muted">{label}: </span>
      <span className="text-[11px] text-text-secondary">{value}</span>
    </div>
  );
}

// ── Image Card ────────────────────────────────────────────────────────────

interface CardProps {
  image: api.ImageRecord;
  onCardClick: (image: api.ImageRecord) => void;
  onDelete: (id: number) => void;
  onUseAsTemplate: (image: api.ImageRecord) => void;
}

function ImageCard({ image, onCardClick, onDelete, onUseAsTemplate }: CardProps) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const imageUrl = `/images/${image.filename}`;
  const promptSnippet =
    image.prompt.length > 60 ? image.prompt.slice(0, 60) + '…' : image.prompt;

  return (
    <div className="relative group rounded-xl overflow-hidden border border-border bg-input-bg aspect-square">
      <img
        src={imageUrl}
        alt={image.prompt}
        loading="lazy"
        className="w-full h-full object-cover transition-transform group-hover:scale-[1.03] cursor-pointer"
        onClick={() => onCardClick(image)}
      />

      {/* Hover overlay */}
      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/50 transition-colors flex flex-col justify-between p-2 pointer-events-none group-hover:pointer-events-auto">
        {/* Top: delete / template */}
        <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={(e) => { e.stopPropagation(); onUseAsTemplate(image); }}
            title="Use as template"
            className="px-2 py-1 rounded-lg bg-accent/80 text-white text-[11px] hover:bg-accent transition-colors cursor-pointer"
          >
            Template
          </button>
          {confirmDelete ? (
            <>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(image.id); }}
                className="px-2 py-1 rounded-lg bg-danger text-white text-[11px] hover:bg-danger/80 transition-colors cursor-pointer"
              >
                Confirm
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); setConfirmDelete(false); }}
                className="px-2 py-1 rounded-lg bg-black/50 text-white text-[11px] cursor-pointer"
              >
                No
              </button>
            </>
          ) : (
            <button
              onClick={(e) => { e.stopPropagation(); setConfirmDelete(true); }}
              title="Delete image"
              className="px-2 py-1 rounded-lg bg-black/60 text-white/80 text-[11px] hover:bg-danger/80 hover:text-white transition-colors cursor-pointer"
            >
              ✕
            </button>
          )}
        </div>

        {/* Bottom: metadata snippet */}
        <div className="opacity-0 group-hover:opacity-100 transition-opacity">
          <p
            className="text-[11px] text-white/90 leading-tight line-clamp-2"
            title={image.prompt}
          >
            {promptSnippet}
          </p>
          {image.model_name && (
            <p className="text-[10px] text-white/60 mt-0.5 truncate">{image.model_name}</p>
          )}
          <p className="text-[10px] text-white/50 mt-0.5">
            {new Date(image.created_at).toLocaleDateString()}
          </p>
        </div>
      </div>
    </div>
  );
}

// ── GalleryView ───────────────────────────────────────────────────────────

const PER_PAGE = 24;

export default function GalleryView() {
  const { dispatch } = useChat();

  const [images, setImages] = useState<api.ImageRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loadingMore, setLoadingMore] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  const [promptFilter, setPromptFilter] = useState('');
  const [modelFilter, setModelFilter] = useState('');
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest'>('newest');

  const [selectedImage, setSelectedImage] = useState<api.ImageRecord | null>(null);

  // ── Fetch helpers ──────────────────────────────────────────────────────

  const fetchPage = useCallback(
    async (targetPage: number, reset: boolean) => {
      if (reset) setInitialLoading(true);
      else setLoadingMore(true);
      try {
        const result = await api.listImagesPaginated({
          page: targetPage,
          per_page: PER_PAGE,
          prompt: promptFilter || undefined,
          model: modelFilter || undefined,
        });
        const sorted = [...result.images].sort((a, b) => {
          const diff =
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          return sortOrder === 'newest' ? -diff : diff;
        });
        setImages((prev) => (reset ? sorted : [...prev, ...sorted]));
        setTotal(result.total);
        setPage(result.page);
      } catch {
        // silent
      } finally {
        if (reset) setInitialLoading(false);
        else setLoadingMore(false);
      }
    },
    [promptFilter, modelFilter, sortOrder],
  );

  // Reset and reload whenever filters/sort change
  useEffect(() => {
    fetchPage(1, true);
  }, [fetchPage]);

  // ── Delete ─────────────────────────────────────────────────────────────

  const handleDelete = useCallback(async (id: number) => {
    try {
      await api.deleteImage(id);
      setImages((prev) => prev.filter((img) => img.id !== id));
      setTotal((t) => t - 1);
    } catch {
      // silent
    }
  }, []);

  // ── Use as template ────────────────────────────────────────────────────

  const handleUseAsTemplate = useCallback(
    (image: api.ImageRecord) => {
      dispatch({
        type: 'SET_IMAGE_TEMPLATE',
        template: {
          prompt: image.prompt,
          negative_prompt: image.negative_prompt ?? '',
          model: image.model_name ?? '',
          sampler: (image.parameters as Record<string, unknown>).sampler ?? 'Euler a',
          steps: (image.parameters as Record<string, unknown>).steps ?? 20,
          cfg_scale: (image.parameters as Record<string, unknown>).cfg_scale ?? 7.0,
          seed: (image.parameters as Record<string, unknown>).seed ?? -1,
          width: image.width,
          height: image.height,
          lora: image.lora_used ?? [],
        },
      });
      dispatch({ type: 'SET_MODE', mode: 'image' });
    },
    [dispatch],
  );

  const hasMore = images.length < total;

  // ── Render ─────────────────────────────────────────────────────────────

  return (
    <div className="flex-1 overflow-hidden flex flex-col">
      {/* Top bar */}
      <div className="shrink-0 px-5 py-4 border-b border-border flex flex-wrap items-center gap-3">
        <h2 className="text-base font-semibold text-text-primary mr-2">Gallery</h2>

        {/* Prompt search */}
        <input
          type="text"
          value={promptFilter}
          onChange={(e) => setPromptFilter(e.target.value)}
          placeholder="Search by prompt…"
          className="flex-1 min-w-[160px] bg-input-bg text-text-primary border border-border rounded-xl px-3 py-1.5 text-sm outline-none focus:border-border-light transition-colors placeholder:text-text-muted"
        />

        {/* Model filter */}
        <input
          type="text"
          value={modelFilter}
          onChange={(e) => setModelFilter(e.target.value)}
          placeholder="Filter by model…"
          className="w-[160px] bg-input-bg text-text-primary border border-border rounded-xl px-3 py-1.5 text-sm outline-none focus:border-border-light transition-colors placeholder:text-text-muted"
        />

        {/* Sort toggle */}
        <button
          onClick={() => setSortOrder((s) => (s === 'newest' ? 'oldest' : 'newest'))}
          className="px-3 py-1.5 rounded-xl border border-border text-text-secondary text-sm hover:bg-button-hover hover:text-text-primary transition-colors cursor-pointer shrink-0"
        >
          {sortOrder === 'newest' ? 'Newest first' : 'Oldest first'}
        </button>

        {/* Count */}
        {!initialLoading && (
          <span className="text-xs text-text-muted shrink-0">
            Showing {images.length} of {total}
          </span>
        )}
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-y-auto px-5 py-5">
        {initialLoading ? (
          <div className="flex items-center justify-center py-24">
            <div className="w-8 h-8 border-2 border-border border-t-accent rounded-full animate-spin" />
          </div>
        ) : images.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 gap-3">
            <p className="text-sm text-text-muted">No images generated yet.</p>
            <p className="text-xs text-text-muted">
              {promptFilter || modelFilter
                ? 'Try clearing the filters.'
                : 'Generate some images to see them here.'}
            </p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {images.map((img) => (
                <ImageCard
                  key={img.id}
                  image={img}
                  onCardClick={setSelectedImage}
                  onDelete={handleDelete}
                  onUseAsTemplate={handleUseAsTemplate}
                />
              ))}
            </div>

            {/* Load more */}
            {hasMore && (
              <div className="flex justify-center mt-6">
                <button
                  onClick={() => fetchPage(page + 1, false)}
                  disabled={loadingMore}
                  className="px-6 py-2.5 rounded-xl border border-border text-text-secondary text-sm hover:bg-button-hover hover:text-text-primary disabled:opacity-50 transition-colors cursor-pointer"
                >
                  {loadingMore ? 'Loading…' : 'Load more'}
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Detail modal */}
      {selectedImage && (
        <DetailModal
          image={selectedImage}
          onClose={() => setSelectedImage(null)}
          onDelete={(id) => {
            handleDelete(id);
            setSelectedImage(null);
          }}
          onUseAsTemplate={handleUseAsTemplate}
        />
      )}
    </div>
  );
}
