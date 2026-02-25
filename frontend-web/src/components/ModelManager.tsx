import { useState, useEffect, useCallback } from 'react';
import { useChat } from '../context/ChatContext';
import * as api from '../api/client';
import type { OllamaModelInfo, OllamaPullProgress } from '../api/client';

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

export default function ModelManager() {
  const { state, refreshOllamaStatus, refreshModels } = useChat();

  const [models, setModels] = useState<OllamaModelInfo[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [error, setError] = useState('');

  // Pull state
  const [pullName, setPullName] = useState('');
  const [pulling, setPulling] = useState(false);
  const [pullProgress, setPullProgress] = useState<OllamaPullProgress | null>(null);
  const [pullStatus, setPullStatus] = useState('');

  // Delete state
  const [deletingModel, setDeletingModel] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  // ── Fetch models ─────────────────────────────────────────────────────

  const fetchModels = useCallback(async () => {
    setLoadingModels(true);
    setError('');
    try {
      const data = await api.ollamaModels();
      setModels(data.models);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load models');
    } finally {
      setLoadingModels(false);
    }
  }, []);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  // ── Pull a model ─────────────────────────────────────────────────────

  const handlePull = () => {
    if (!pullName.trim() || pulling) return;

    setPulling(true);
    setPullProgress(null);
    setPullStatus('Starting download...');

    api.ollamaPull(
      pullName.trim(),
      (progress) => {
        setPullProgress(progress);
        setPullStatus(progress.status);
      },
      () => {
        setPulling(false);
        setPullProgress(null);
        setPullStatus('');
        setPullName('');
        // Refresh everything
        fetchModels();
        refreshOllamaStatus();
        refreshModels();
      },
      (err) => {
        setPulling(false);
        setPullProgress(null);
        setPullStatus(`Error: ${err}`);
      },
    );
  };

  // ── Delete a model ───────────────────────────────────────────────────

  const handleDelete = async (name: string) => {
    setDeletingModel(name);
    try {
      await api.ollamaDelete(name);
      setModels((prev) => prev.filter((m) => m.name !== name));
      refreshOllamaStatus();
      refreshModels();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete model');
    } finally {
      setDeletingModel(null);
      setConfirmDelete(null);
    }
  };

  // ── Pull progress bar ────────────────────────────────────────────────

  const progressPercent =
    pullProgress && pullProgress.total > 0
      ? Math.round((pullProgress.completed / pullProgress.total) * 100)
      : 0;

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-text-primary">Model Manager</h1>
            <p className="text-sm text-text-secondary mt-1">
              {state.ollamaOnline ? (
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
                  Ollama connected · {models.length} model{models.length !== 1 ? 's' : ''}
                </span>
              ) : (
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
                  Ollama offline
                </span>
              )}
            </p>
          </div>

          <button
            onClick={fetchModels}
            disabled={loadingModels}
            className="px-3 py-1.5 text-xs rounded-md bg-button-hover text-text-secondary hover:text-text-primary transition-colors cursor-pointer disabled:opacity-50"
          >
            {loadingModels ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 px-4 py-2 bg-red-500/10 border border-red-500/30 rounded-md text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Pull model */}
        <div className="mb-6 p-4 rounded-lg bg-sidebar-bg border border-border">
          <h2 className="text-sm font-semibold text-text-primary mb-3">Pull a Model</h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={pullName}
              onChange={(e) => setPullName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handlePull()}
              placeholder="e.g. llama3, mistral, gemma2..."
              disabled={pulling}
              className="flex-1 bg-main-bg text-text-primary text-sm border border-border rounded-md px-3 py-2 outline-none focus:border-accent transition-colors placeholder:text-text-muted disabled:opacity-50"
            />
            <button
              onClick={handlePull}
              disabled={pulling || !pullName.trim()}
              className="px-4 py-2 rounded-md bg-accent text-white text-sm font-medium hover:bg-accent/80 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {pulling ? 'Pulling...' : 'Pull'}
            </button>
          </div>

          {/* Progress bar */}
          {pulling && (
            <div className="mt-3">
              <div className="flex justify-between text-xs text-text-secondary mb-1">
                <span>{pullStatus}</span>
                {pullProgress && pullProgress.total > 0 && (
                  <span>
                    {formatBytes(pullProgress.completed)} / {formatBytes(pullProgress.total)} ({progressPercent}%)
                  </span>
                )}
              </div>
              <div className="w-full h-2 bg-main-bg rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent rounded-full transition-all duration-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
          )}

          {/* Pull status message (after completion or error) */}
          {!pulling && pullStatus && (
            <p className={`mt-2 text-xs ${pullStatus.startsWith('Error') ? 'text-red-400' : 'text-green-400'}`}>
              {pullStatus}
            </p>
          )}
        </div>

        {/* Model list */}
        <div className="rounded-lg bg-sidebar-bg border border-border overflow-hidden">
          <div className="px-4 py-3 border-b border-border">
            <h2 className="text-sm font-semibold text-text-primary">Installed Models</h2>
          </div>

          {loadingModels && models.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-text-muted">Loading models...</div>
          ) : models.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-text-muted">
              No models installed. Pull one above to get started.
            </div>
          ) : (
            <ul>
              {models.map((model) => (
                <li
                  key={model.name}
                  className="flex items-center gap-3 px-4 py-3 border-b border-border last:border-b-0 hover:bg-button-hover/50 transition-colors"
                >
                  {/* Model info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-text-primary truncate">{model.name}</p>
                    <div className="flex items-center gap-3 mt-0.5">
                      <span className="text-xs text-text-muted">{formatBytes(model.size)}</span>
                      {model.family && (
                        <span className="text-xs text-text-muted">{model.family}</span>
                      )}
                      {model.parameter_size && (
                        <span className="text-xs text-text-muted">{model.parameter_size}</span>
                      )}
                      {model.quantization_level && (
                        <span className="text-xs text-accent/70">{model.quantization_level}</span>
                      )}
                    </div>
                  </div>

                  {/* Delete button */}
                  {confirmDelete === model.name ? (
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => handleDelete(model.name)}
                        disabled={deletingModel === model.name}
                        className="px-2 py-1 text-xs rounded bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors cursor-pointer disabled:opacity-50"
                      >
                        {deletingModel === model.name ? '...' : 'Confirm'}
                      </button>
                      <button
                        onClick={() => setConfirmDelete(null)}
                        className="px-2 py-1 text-xs rounded text-text-muted hover:text-text-secondary transition-colors cursor-pointer"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setConfirmDelete(model.name)}
                      className="p-1.5 rounded text-text-muted hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                      title={`Delete ${model.name}`}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                        <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
