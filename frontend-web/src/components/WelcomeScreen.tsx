import { useState, useCallback } from 'react';
import { useChat } from '../context/ChatContext';
import PersonaPicker from './PersonaPicker';

export default function WelcomeScreen() {
  const { state, dispatch } = useChat();
  const [pickerOpen, setPickerOpen] = useState(false);

  const handleSelectPersona = useCallback(
    (id: number) => {
      const persona = state.personas.find((p) => p.id === id);
      if (persona) {
        dispatch({ type: 'SELECT_PERSONA', persona });
      }
    },
    [state.personas, dispatch],
  );

  // Show first 5 personas as quick chips
  const quickPersonas = state.personas.slice(0, 5);

  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-6 px-4">
      <h1 className="text-[28px] font-semibold text-text-primary select-none">
        How can I help you today?
      </h1>

      {/* Persona chips */}
      <div className="flex flex-wrap justify-center gap-2">
        {quickPersonas.map((p) => {
          const isSelected = state.selectedPersona?.id === p.id;
          return (
            <button
              key={p.id}
              onClick={() => handleSelectPersona(p.id)}
              className={[
                'flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-sm transition-colors cursor-pointer',
                isSelected
                  ? 'bg-accent/20 border-accent/40 text-text-primary'
                  : 'border-border text-text-secondary hover:bg-button-hover hover:text-text-primary',
              ].join(' ')}
            >
              <span>{p.icon}</span>
              <span>{p.name}</span>
            </button>
          );
        })}

        {/* + Custom chip */}
        <button
          onClick={() => setPickerOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-dashed border-border text-text-muted text-sm hover:border-border-light hover:text-text-secondary transition-colors cursor-pointer"
        >
          + Custom
        </button>
      </div>

      {/* Full persona picker modal */}
      <PersonaPicker open={pickerOpen} onClose={() => setPickerOpen(false)} />
    </div>
  );
}
