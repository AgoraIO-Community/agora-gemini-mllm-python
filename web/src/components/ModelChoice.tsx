'use client';

export const DEMO_MODELS = {
  live: 'models/gemini-3.8-live',
  extendedThinking: 'models/gemini-3.8-live-extended-thinking',
} as const;
export type DemoModel = (typeof DEMO_MODELS)[keyof typeof DEMO_MODELS];
export type ThinkingLevel = 'low' | 'medium' | 'high';

const THINKING_LEVELS: ThinkingLevel[] = ['low', 'medium', 'high'];

export function ModelChoice({ model, onModelChange, thinkingLevel, onThinkingLevelChange, disabled = false }: {
  model: DemoModel;
  onModelChange: (model: DemoModel) => void;
  thinkingLevel: ThinkingLevel;
  onThinkingLevelChange: (level: ThinkingLevel) => void;
  disabled?: boolean;
}) {
  return <div className="mt-6 w-full text-left">
    <span className="text-sm font-medium text-white">Choose a Gemini model</span>
    <div className="mt-2 grid grid-cols-2 gap-2" role="group" aria-label="Gemini model">
      {([DEMO_MODELS.live, DEMO_MODELS.extendedThinking] as DemoModel[]).map(choice =>
        <button key={choice} type="button" disabled={disabled} aria-pressed={model === choice}
          onClick={() => onModelChange(choice)}
          className={`rounded-lg border px-3 py-3 text-sm transition-colors disabled:opacity-60 ${model === choice ? 'border-primary bg-primary/15 text-white' : 'border-[#444] text-muted-foreground hover:border-white'}`}>
          {choice === DEMO_MODELS.live ? 'Gemini 3.8 Live' : 'Gemini 3.8 Live Extended Thinking'}
        </button>) }
    </div>
    {model === DEMO_MODELS.extendedThinking && <div className="mt-5">
      <label htmlFor="thinking-level" className="flex justify-between text-sm font-medium text-white">
        <span>Thinking level</span><span className="capitalize">{thinkingLevel}</span>
      </label>
      <input id="thinking-level" type="range" min={0} max={2} step={1}
        value={THINKING_LEVELS.indexOf(thinkingLevel)} disabled={disabled}
        onChange={event => onThinkingLevelChange(THINKING_LEVELS[Number(event.target.value)])}
        aria-valuetext={thinkingLevel} className="mt-3 w-full accent-primary" />
      <div className="flex justify-between text-xs text-muted-foreground"><span>Low</span><span>Medium</span><span>High</span></div>
    </div>}
  </div>;
}
