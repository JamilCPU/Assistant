import { useState, useCallback } from 'react';
import { useChat } from '../context/ChatContext';
import * as api from '../api/client';

interface PersonaPickerProps {
  /** When true, show the full picker modal overlay. */
  open: boolean;
  onClose: () => void;
}

export default function PersonaPicker({ open, onClose }: PersonaPickerProps) {
  const { state, dispatch, refreshPersonas } = useChat();

  // ── New persona form state ───────────────────────────────────────────
  const [showNewForm, setShowNewForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newIcon, setNewIcon] = useState('🤖');
  const [newPrompt, setNewPrompt] = useState('');
  const [newModel, setNewModel] = useState('');
  const [saving, setSaving] = useState(false);

  // ── Custom prompt entry ──────────────────────────────────────────────
  const [showCustom, setShowCustom] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');

  const handleSelectPersona = useCallback(
    (persona: api.Persona) => {
      dispatch({ type: 'SELECT_PERSONA', persona });
      setShowCustom(false);
      onClose();
    },
    [dispatch, onClose],
  );

  const handleCustom = useCallback(() => {
    dispatch({ type: 'SELECT_PERSONA', persona: null });
    setShowCustom(true);
  }, [dispatch]);

  const handleApplyCustom = useCallback(() => {
    dispatch({ type: 'SET_SYSTEM_PROMPT', prompt: customPrompt });
    onClose();
  }, [dispatch, customPrompt, onClose]);

  const handleDeletePersona = useCallback(
    async (e: React.MouseEvent, id: number) => {
      e.stopPropagation();
      try {
        await api.deletePersona(id);
        await refreshPersonas();
      } catch {
        // silently ignore
      }
    },
    [refreshPersonas],
  );

  const handleCreatePersona = useCallback(async () => {
    if (!newName.trim() || !newPrompt.trim()) return;
    setSaving(true);
    try {
      await api.createPersona({
        name: newName.trim(),
        system_prompt: newPrompt.trim(),
        icon: newIcon || '🤖',
        default_model: newModel.trim() || null,
      });
      await refreshPersonas();
      setNewName('');
      setNewIcon('🤖');
      setNewPrompt('');
      setNewModel('');
      setShowNewForm(false);
    } catch {
      // silently ignore
    } finally {
      setSaving(false);
    }
  }, [newName, newIcon, newPrompt, newModel, refreshPersonas]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="bg-sidebar-bg border border-border rounded-xl shadow-2xl w-full max-w-lg mx-4 p-5 max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-text-primary font-semibold text-base">Personas</h2>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-primary text-lg leading-none cursor-pointer"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Persona grid */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          {state.personas.map((p) => {
            const isSelected = state.selectedPersona?.id === p.id;
            return (
              <div
                key={p.id}
                onClick={() => handleSelectPersona(p)}
                className={[
                  'relative group rounded-lg border p-3 cursor-pointer transition-colors text-center',
                  isSelected
                    ? 'bg-accent/20 border-accent/40 text-text-primary'
                    : 'border-border hover:bg-button-hover text-text-secondary',
                ].join(' ')}
              >
                <div className="text-2xl mb-1">{p.icon}</div>
                <div className="text-xs font-medium text-text-primary truncate">{p.name}</div>
                {!p.is_builtin && (
                  <button
                    onClick={(e) => handleDeletePersona(e, p.id)}
                    className="absolute top-1 right-1 text-text-muted hover:text-danger text-xs opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                    aria-label="Delete persona"
                  >
                    ✕
                  </button>
                )}
              </div>
            );
          })}

          {/* Custom card */}
          <div
            onClick={handleCustom}
            className={[
              'rounded-lg border p-3 cursor-pointer transition-colors text-center',
              showCustom
                ? 'bg-accent/20 border-accent/40 text-text-primary'
                : 'border-border hover:bg-button-hover text-text-secondary',
            ].join(' ')}
          >
            <div className="text-2xl mb-1">✏️</div>
            <div className="text-xs font-medium text-text-primary">Custom</div>
          </div>
        </div>

        {/* Custom prompt textarea */}
        {showCustom && (
          <div className="mb-4">
            <label className="block text-xs text-text-secondary mb-1">Custom system prompt</label>
            <textarea
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              rows={4}
              placeholder="Enter a custom system prompt…"
              className="w-full bg-input-bg border border-border rounded-md px-3 py-2 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent resize-none"
            />
            <button
              onClick={handleApplyCustom}
              className="mt-2 bg-accent hover:bg-accent-hover text-white text-xs font-medium px-3 py-1.5 rounded-md transition-colors cursor-pointer"
            >
              Apply
            </button>
          </div>
        )}

        {/* New persona form toggle */}
        {!showNewForm ? (
          <button
            onClick={() => setShowNewForm(true)}
            className="w-full border border-dashed border-border rounded-lg py-2 text-xs text-text-muted hover:text-text-secondary hover:border-border-light transition-colors cursor-pointer"
          >
            + New persona
          </button>
        ) : (
          <div className="border border-border rounded-lg p-3 mt-2">
            <div className="text-xs font-medium text-text-secondary mb-3">New persona</div>
            <div className="flex gap-2 mb-2">
              <input
                value={newIcon}
                onChange={(e) => setNewIcon(e.target.value)}
                placeholder="🤖"
                maxLength={2}
                className="w-12 bg-input-bg border border-border rounded-md px-2 py-1.5 text-center text-sm text-text-primary outline-none focus:border-accent"
              />
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Persona name"
                className="flex-1 bg-input-bg border border-border rounded-md px-2 py-1.5 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent"
              />
            </div>
            <textarea
              value={newPrompt}
              onChange={(e) => setNewPrompt(e.target.value)}
              rows={3}
              placeholder="System prompt…"
              className="w-full bg-input-bg border border-border rounded-md px-2 py-1.5 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent resize-none mb-2"
            />
            <input
              value={newModel}
              onChange={(e) => setNewModel(e.target.value)}
              placeholder="Default model (optional)"
              className="w-full bg-input-bg border border-border rounded-md px-2 py-1.5 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent mb-2"
            />
            <div className="flex gap-2">
              <button
                onClick={handleCreatePersona}
                disabled={saving || !newName.trim() || !newPrompt.trim()}
                className="bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-md transition-colors cursor-pointer"
              >
                {saving ? 'Saving…' : 'Create'}
              </button>
              <button
                onClick={() => setShowNewForm(false)}
                className="text-text-muted hover:text-text-secondary text-xs px-3 py-1.5 rounded-md transition-colors cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
