import { StatusItem } from "./VoiceBlocks.jsx";

export function VoiceControls({
  autoContinue,
  isBusy,
  isRecording,
  language,
  languages,
  onAutoContinueChange,
  onLanguageChange,
  onStart,
  onStop,
  provider,
  speechStatus,
  status,
  intent,
}) {
  return (
    <>
      <fieldset>
        <legend>Language</legend>
        <div className="segmented">
          {languages.map((item) => (
            <button
              className={language === item.id ? "selected" : ""}
              disabled={isBusy}
              key={item.id}
              onClick={() => onLanguageChange(item.id)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </div>
      </fieldset>

      <label className="voice-toggle">
        <input
          checked={autoContinue}
          disabled={isBusy}
          onChange={(event) => onAutoContinueChange(event.target.checked)}
          type="checkbox"
        />
        <span>Auto continue</span>
      </label>

      <div className="voice-actions">
        <button className="primary-action" disabled={isBusy} onClick={onStart} type="button">
          Start
        </button>
        <button className="secondary-action" disabled={!isRecording} onClick={onStop} type="button">
          Stop
        </button>
      </div>

      <div className="voice-status-grid" aria-label="Voice status">
        <StatusItem label="Microphone" value={status} />
        <StatusItem label="Speech" value={speechStatus} />
        <StatusItem label="Intent" value={intent} />
        <StatusItem label="Provider" value={provider} />
      </div>
    </>
  );
}
