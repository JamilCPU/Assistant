import { useState, useEffect, useCallback } from 'react';
import * as api from '../api/client';
import { useChat } from '../context/ChatContext';

// ── Types ─────────────────────────────────────────────────────────────────

type Tab = 'chat' | 'image' | 'tts' | 'tools' | 'server';

interface Props {
  onClose: () => void;
}

// ── SettingsModal ─────────────────────────────────────────────────────────

export default function SettingsModal({ onClose }: Props) {
  const { state, dispatch, loadSettings } = useChat();
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [settings, setSettings] = useState<api.UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [newAllowlistPath, setNewAllowlistPath] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);

  // ── Load settings on open ──────────────────────────────────────────────

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getSettings();
      setSettings(data);
    } catch {
      // Keep null — show error state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  // ── Keyboard: Escape closes modal ─────────────────────────────────────

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  // ── Save ──────────────────────────────────────────────────────────────

  const handleSave = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      const updated = await api.updateSettings({
        chat: settings.chat,
        image: settings.image,
        tts: settings.tts,
        tools: settings.tools,
        server: settings.server,
      });
      setSettings(updated);
      // Sync system prompt default into context
      dispatch({
        type: 'SET_SYSTEM_PROMPT_DEFAULT',
        prompt: updated.chat.system_prompt,
      });
      await loadSettings();
      setToast('Settings saved');
      setTimeout(() => setToast(null), 3000);
    } catch {
      setToast('Failed to save settings');
      setTimeout(() => setToast(null), 3000);
    } finally {
      setSaving(false);
    }
  };

  // ── Helpers ───────────────────────────────────────────────────────────

  function updateChat(patch: Partial<api.ChatSettings>) {
    if (!settings) return;
    setSettings({ ...settings, chat: { ...settings.chat, ...patch } });
  }

  function updateImage(patch: Partial<api.ImageSettings>) {
    if (!settings) return;
    setSettings({ ...settings, image: { ...settings.image, ...patch } });
  }

  function updateTTS(patch: Partial<api.TTSSettings>) {
    if (!settings) return;
    setSettings({ ...settings, tts: { ...settings.tts, ...patch } });
  }

  function updateTools(patch: Partial<api.ToolsSettings>) {
    if (!settings) return;
    setSettings({ ...settings, tools: { ...settings.tools, ...patch } });
  }

  function updateServer(patch: Partial<api.ServerSettings>) {
    if (!settings) return;
    setSettings({ ...settings, server: { ...settings.server, ...patch } });
  }

  function addAllowlistPath() {
    const trimmed = newAllowlistPath.trim();
    if (!trimmed || !settings) return;
    if (settings.tools.filesystem_allowlist.includes(trimmed)) return;
    updateTools({ filesystem_allowlist: [...settings.tools.filesystem_allowlist, trimmed] });
    setNewAllowlistPath('');
  }

  function removeAllowlistPath(path: string) {
    if (!settings) return;
    updateTools({
      filesystem_allowlist: settings.tools.filesystem_allowlist.filter((p) => p !== path),
    });
  }

  // ── Tab label helper ──────────────────────────────────────────────────

  const tabs: { key: Tab; label: string }[] = [
    { key: 'chat', label: 'Chat' },
    { key: 'image', label: 'Image' },
    { key: 'tts', label: 'TTS' },
    { key: 'tools', label: 'Tools' },
    { key: 'server', label: 'Server' },
  ];

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl max-h-[90vh] bg-sidebar-bg border border-border rounded-2xl shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border shrink-0">
          <h2 className="text-base font-semibold text-text-primary">Settings</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-text-secondary hover:bg-button-hover hover:text-text-primary transition-colors cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-0.5 px-6 pt-3 shrink-0">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`px-4 py-1.5 rounded-t-lg text-sm font-medium transition-colors cursor-pointer ${
                activeTab === t.key
                  ? 'bg-button-active text-text-primary'
                  : 'text-text-secondary hover:text-text-primary hover:bg-button-hover'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="w-6 h-6 border-2 border-border border-t-accent rounded-full animate-spin" />
            </div>
          ) : !settings ? (
            <p className="text-sm text-danger">Failed to load settings.</p>
          ) : (
            <>
              {/* ── Chat Tab ────────────────────────────────────────────── */}
              {activeTab === 'chat' && (
                <div className="flex flex-col gap-5">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-text-secondary tracking-wide">
                      Default Model
                    </label>
                    <select
                      value={settings.chat.default_model}
                      onChange={(e) => updateChat({ default_model: e.target.value })}
                      className="w-full bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2 text-sm outline-none focus:border-border-light transition-colors cursor-pointer"
                    >
                      <option value="">— none —</option>
                      {state.chatModels.map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-text-secondary tracking-wide">
                      System Prompt
                    </label>
                    <textarea
                      value={settings.chat.system_prompt}
                      onChange={(e) => updateChat({ system_prompt: e.target.value })}
                      rows={5}
                      placeholder="Instructions sent with every new conversation…"
                      className="w-full bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2.5 text-sm outline-none focus:border-border-light resize-none transition-colors placeholder:text-text-muted"
                    />
                  </div>
                </div>
              )}

              {/* ── Image Tab ───────────────────────────────────────────── */}
              {activeTab === 'image' && (
                <div className="flex flex-col gap-5">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-text-secondary tracking-wide">
                      Default Checkpoint
                    </label>
                    <input
                      type="text"
                      value={settings.image.default_model}
                      onChange={(e) => updateImage({ default_model: e.target.value })}
                      placeholder="Model / checkpoint name"
                      className="w-full bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2 text-sm outline-none focus:border-border-light transition-colors placeholder:text-text-muted"
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-text-secondary tracking-wide">
                      Default Sampler
                    </label>
                    <input
                      type="text"
                      value={settings.image.default_sampler}
                      onChange={(e) => updateImage({ default_sampler: e.target.value })}
                      placeholder="e.g. Euler a"
                      className="w-full bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2 text-sm outline-none focus:border-border-light transition-colors placeholder:text-text-muted"
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-text-secondary tracking-wide">
                        Default Steps
                      </span>
                      <span className="text-xs text-text-muted">{settings.image.default_steps}</span>
                    </div>
                    <input
                      type="range"
                      min={1} max={100} step={1}
                      value={settings.image.default_steps}
                      onChange={(e) => updateImage({ default_steps: parseInt(e.target.value, 10) })}
                      className="w-full h-1.5 appearance-none bg-border rounded-full outline-none cursor-pointer accent-accent"
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-text-secondary tracking-wide">
                        Default CFG Scale
                      </span>
                      <span className="text-xs text-text-muted">{settings.image.default_cfg}</span>
                    </div>
                    <input
                      type="range"
                      min={1} max={20} step={0.5}
                      value={settings.image.default_cfg}
                      onChange={(e) => updateImage({ default_cfg: parseFloat(e.target.value) })}
                      className="w-full h-1.5 appearance-none bg-border rounded-full outline-none cursor-pointer accent-accent"
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-text-secondary tracking-wide">
                      Default Size
                    </label>
                    <div className="flex gap-3 items-center">
                      <div className="flex flex-col gap-1 flex-1">
                        <span className="text-[11px] text-text-muted">Width</span>
                        <input
                          type="number"
                          value={settings.image.default_width}
                          min={64} max={2048} step={64}
                          onChange={(e) => {
                            const v = parseInt(e.target.value, 10);
                            if (!isNaN(v)) updateImage({ default_width: v });
                          }}
                          className="w-full bg-input-bg text-text-primary border border-border rounded-lg px-2.5 py-1.5 text-sm outline-none focus:border-border-light transition-colors"
                        />
                      </div>
                      <span className="text-text-muted mt-4">×</span>
                      <div className="flex flex-col gap-1 flex-1">
                        <span className="text-[11px] text-text-muted">Height</span>
                        <input
                          type="number"
                          value={settings.image.default_height}
                          min={64} max={2048} step={64}
                          onChange={(e) => {
                            const v = parseInt(e.target.value, 10);
                            if (!isNaN(v)) updateImage({ default_height: v });
                          }}
                          className="w-full bg-input-bg text-text-primary border border-border rounded-lg px-2.5 py-1.5 text-sm outline-none focus:border-border-light transition-colors"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ── TTS Tab ─────────────────────────────────────────────── */}
              {activeTab === 'tts' && (
                <div className="flex flex-col gap-5">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <div
                      onClick={() => updateTTS({ enabled: !settings.tts.enabled })}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors cursor-pointer ${
                        settings.tts.enabled ? 'bg-accent' : 'bg-border'
                      }`}
                    >
                      <span
                        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                          settings.tts.enabled ? 'translate-x-4' : 'translate-x-0.5'
                        }`}
                      />
                    </div>
                    <span className="text-sm text-text-primary">Enable TTS</span>
                  </label>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-text-secondary tracking-wide">
                      Default Voice
                    </label>
                    <input
                      type="text"
                      value={settings.tts.default_voice}
                      onChange={(e) => updateTTS({ default_voice: e.target.value })}
                      placeholder="e.g. en_US-lessac-medium"
                      className="w-full bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2 text-sm outline-none focus:border-border-light transition-colors placeholder:text-text-muted"
                    />
                  </div>
                </div>
              )}

              {/* ── Tools Tab ───────────────────────────────────────────── */}
              {activeTab === 'tools' && (
                <div className="flex flex-col gap-5">
                  <div className="flex flex-col gap-2">
                    <label className="text-xs font-semibold text-text-secondary tracking-wide">
                      Filesystem Allowlist
                    </label>
                    {settings.tools.filesystem_allowlist.length === 0 ? (
                      <p className="text-xs text-text-muted">No paths added yet.</p>
                    ) : (
                      <ul className="flex flex-col gap-1">
                        {settings.tools.filesystem_allowlist.map((path) => (
                          <li
                            key={path}
                            className="flex items-center justify-between gap-2 bg-input-bg border border-border rounded-lg px-3 py-1.5"
                          >
                            <span className="text-sm text-text-primary font-mono truncate">{path}</span>
                            <button
                              onClick={() => removeAllowlistPath(path)}
                              className="text-text-muted hover:text-danger transition-colors text-xs shrink-0 cursor-pointer"
                            >
                              Remove
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                    <div className="flex gap-2 mt-1">
                      <input
                        type="text"
                        value={newAllowlistPath}
                        onChange={(e) => setNewAllowlistPath(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addAllowlistPath(); } }}
                        placeholder="C:/Users/…"
                        className="flex-1 bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2 text-sm outline-none focus:border-border-light transition-colors placeholder:text-text-muted"
                      />
                      <button
                        onClick={addAllowlistPath}
                        className="px-4 py-2 rounded-xl bg-accent text-white text-sm font-medium hover:bg-accent-hover transition-colors cursor-pointer"
                      >
                        Add
                      </button>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-text-secondary tracking-wide">
                        Max File Size (MB)
                      </span>
                      <span className="text-xs text-text-muted">{settings.tools.max_file_size_mb} MB</span>
                    </div>
                    <input
                      type="range"
                      min={1} max={100} step={1}
                      value={settings.tools.max_file_size_mb}
                      onChange={(e) => updateTools({ max_file_size_mb: parseInt(e.target.value, 10) })}
                      className="w-full h-1.5 appearance-none bg-border rounded-full outline-none cursor-pointer accent-accent"
                    />
                  </div>
                </div>
              )}

              {/* ── Server Tab ──────────────────────────────────────────── */}
              {activeTab === 'server' && (
                <div className="flex flex-col gap-5">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-text-secondary tracking-wide">
                      API Key
                    </label>
                    <div className="relative">
                      <input
                        type={showApiKey ? 'text' : 'password'}
                        value={settings.server.api_key}
                        onChange={(e) => updateServer({ api_key: e.target.value })}
                        placeholder="Leave blank to disable auth"
                        className="w-full bg-input-bg text-text-primary border border-border rounded-xl px-3 py-2 pr-12 text-sm outline-none focus:border-border-light transition-colors placeholder:text-text-muted"
                      />
                      <button
                        type="button"
                        onClick={() => setShowApiKey((v) => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary transition-colors text-xs cursor-pointer"
                      >
                        {showApiKey ? 'Hide' : 'Show'}
                      </button>
                    </div>
                    <p className="text-xs text-text-muted">
                      Setting an API key requires all requests to include{' '}
                      <code className="font-mono">X-API-Key</code> header.
                    </p>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-border shrink-0">
          {toast ? (
            <span className="text-sm text-accent">{toast}</span>
          ) : (
            <span />
          )}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-border text-text-secondary text-sm hover:bg-button-hover hover:text-text-primary transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving || loading || !settings}
              className="px-5 py-2 rounded-xl bg-accent text-white text-sm font-semibold hover:bg-accent-hover disabled:bg-border disabled:text-text-muted transition-colors cursor-pointer"
            >
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
