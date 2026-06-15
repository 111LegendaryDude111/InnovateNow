import { useEffect, useRef, useState } from "react";
import { createVoiceAssistantResponse } from "./voiceCommands.js";
import {
  describeRecognitionError,
  getSpeechRecognitionConstructor,
  hasSpeechSynthesis,
  speakResponse,
} from "./voiceSpeech.js";

const LANGUAGES = [
  { id: "ru", label: "RU", recognitionLang: "ru-RU", speechLang: "ru-RU" },
  { id: "en", label: "EN", recognitionLang: "en-US", speechLang: "en-US" },
];

function VoicePage() {
  const [language, setLanguage] = useState("ru");
  const [status, setStatus] = useState("idle");
  const [speechStatus, setSpeechStatus] = useState("idle");
  const [transcript, setTranscript] = useState("");
  const [assistantText, setAssistantText] = useState("");
  const [intent, setIntent] = useState("none");
  const [error, setError] = useState("");
  const recognitionRef = useRef(null);

  const selectedLanguage = LANGUAGES.find((item) => item.id === language);
  const isListening = status === "listening" || status === "starting";

  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
      window.speechSynthesis?.cancel();
    };
  }, []);

  function handleStart() {
    const SpeechRecognition = getSpeechRecognitionConstructor();
    if (!SpeechRecognition) {
      setStatus("error");
      setError("Speech Recognition is not supported in this browser.");
      return;
    }
    if (!hasSpeechSynthesis()) {
      setStatus("error");
      setError("Text-to-Speech is not supported in this browser.");
      return;
    }

    setError("");
    setTranscript("");
    setAssistantText("");
    setIntent("none");
    setSpeechStatus("idle");

    const recognition = new SpeechRecognition();
    recognition.lang = selectedLanguage.recognitionLang;
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setStatus("listening");
    recognition.onresult = (event) => handleRecognitionResult(event, selectedLanguage);
    recognition.onnomatch = () => {
      setStatus("error");
      setError("Speech was not recognized. Try again.");
    };
    recognition.onerror = (event) => {
      recognitionRef.current = null;
      setStatus("error");
      setError(describeRecognitionError(event.error));
    };
    recognition.onend = () => {
      if (recognitionRef.current === recognition) {
        recognitionRef.current = null;
        setStatus((current) => (current === "listening" ? "idle" : current));
      }
    };

    try {
      recognitionRef.current = recognition;
      setStatus("starting");
      recognition.start();
    } catch (startError) {
      recognitionRef.current = null;
      setStatus("error");
      setError(startError.message);
    }
  }

  function handleStop() {
    const recognition = recognitionRef.current;
    recognitionRef.current = null;
    recognition?.stop();
    setStatus("idle");
  }

  function handleRecognitionResult(event, activeLanguage) {
    const text = event.results?.[0]?.[0]?.transcript?.trim() ?? "";
    setTranscript(text);

    if (!text) {
      setStatus("error");
      setError("Speech was not recognized. Try again.");
      return;
    }

    setStatus("processing");
    const response = createVoiceAssistantResponse(text, {
      language: activeLanguage.id,
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    });
    setIntent(response.intent);
    setAssistantText(response.responseText);
    setStatus("done");
    speakResponse(response.responseText, activeLanguage.speechLang, setSpeechStatus, setError);
  }

  return (
    <section className="workspace voice-workspace">
      <section className="control-panel">
        <div className="brand-row">
          <div>
            <p className="eyebrow">Web Speech</p>
            <h2>Microphone</h2>
          </div>
          <span className={`status status-${status}`}>{status}</span>
        </div>

        <fieldset>
          <legend>Language</legend>
          <div className="segmented">
            {LANGUAGES.map((item) => (
              <button
                className={language === item.id ? "selected" : ""}
                disabled={isListening}
                key={item.id}
                onClick={() => setLanguage(item.id)}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </div>
        </fieldset>

        <div className="voice-actions">
          <button className="primary-action" disabled={isListening} onClick={handleStart} type="button">
            Start
          </button>
          <button className="secondary-action" disabled={!isListening} onClick={handleStop} type="button">
            Stop
          </button>
        </div>

        <div className="voice-status-grid" aria-label="Voice status">
          <StatusItem label="Microphone" value={status} />
          <StatusItem label="Speech" value={speechStatus} />
          <StatusItem label="Intent" value={intent} />
        </div>

        {error ? <p className="error">{error}</p> : null}
      </section>

      <section className="voice-panel" aria-live="polite">
        <div className="response-header">
          <div>
            <p className="eyebrow">Transcript</p>
            <h2>Assistant Response</h2>
          </div>
        </div>

        <div className="voice-output">
          <OutputBlock label="Recognized" value={transcript || "No transcript yet."} />
          <OutputBlock label="Response" value={assistantText || "Response will appear here."} />
        </div>
      </section>
    </section>
  );
}

function StatusItem({ label, value }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function OutputBlock({ label, value }) {
  return (
    <article>
      <span>{label}</span>
      <p>{value}</p>
    </article>
  );
}

export default VoicePage;
