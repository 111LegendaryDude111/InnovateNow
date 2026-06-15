import { useEffect, useRef, useState } from "react";
import { OutputBlock } from "./VoiceBlocks.jsx";
import { VoiceControls } from "./VoiceControls.jsx";
import { requestVoiceResponse } from "./api.js";
import { playVoiceAudio } from "./voiceAudio.js";
import {
  createAudioBlob,
  getSupportedAudioMimeType,
  hasAudioRecording,
  stopStream,
} from "./voiceRecording.js";

const LANGUAGES = [
  { id: "ru", label: "RU" },
  { id: "en", label: "EN" },
];

function VoicePage() {
  const [language, setLanguage] = useState("ru");
  const [status, setStatus] = useState("idle");
  const [speechStatus, setSpeechStatus] = useState("idle");
  const [transcript, setTranscript] = useState("");
  const [assistantText, setAssistantText] = useState("");
  const [intent, setIntent] = useState("none");
  const [provider, setProvider] = useState("server");
  const [autoContinue, setAutoContinue] = useState(false);
  const [error, setError] = useState("");
  const recorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const autoContinueRef = useRef(false);

  const selectedLanguage = LANGUAGES.find((item) => item.id === language);
  const isRecording = status === "recording" || status === "starting";
  const isBusy = isRecording || status === "transcribing";

  useEffect(() => {
    autoContinueRef.current = autoContinue;
  }, [autoContinue]);

  useEffect(() => {
    return () => {
      recorderRef.current?.stop();
      stopStream(streamRef.current);
    };
  }, []);

  async function handleStart() {
    if (!hasAudioRecording()) {
      setStatus("error");
      setError("Audio recording is not supported in this browser.");
      return;
    }
    resetOutput();
    try {
      setStatus("starting");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      startRecorder(stream, selectedLanguage);
    } catch (recordingError) {
      setStatus("error");
      setError(recordingError.message);
      stopStream(streamRef.current);
    }
  }

  function startRecorder(stream, activeLanguage) {
    const mimeType = getSupportedAudioMimeType();
    const options = mimeType ? { mimeType } : undefined;
    const recorder = new MediaRecorder(stream, options);

    chunksRef.current = [];
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };
    recorder.onerror = (event) => {
      recorderRef.current = null;
      setStatus("error");
      setError(event.error?.message || "Audio recording failed.");
      stopStream(stream);
    };
    recorder.onstart = () => setStatus("recording");
    recorder.onstop = () => handleRecordingStop(recorder, activeLanguage);

    recorderRef.current = recorder;
    recorder.start();
  }

  function handleStop() {
    if (recorderRef.current?.state === "recording") {
      recorderRef.current.stop();
    }
  }

  async function handleRecordingStop(recorder, activeLanguage) {
    recorderRef.current = null;
    stopStream(streamRef.current);
    const audioBlob = createAudioBlob(chunksRef.current, recorder.mimeType);
    chunksRef.current = [];

    if (!audioBlob.size) {
      setStatus("error");
      setError("Audio recording is empty. Try again.");
      return;
    }

    setStatus("transcribing");
    try {
      const result = await requestVoiceResponse({
        audioBlob,
        language: activeLanguage.id,
      });
      setTranscript(result.transcript);
      setAssistantText(result.response_text);
      setIntent(result.intent);
      setProvider(`${result.stt_provider} + ${result.llm_provider} + ${result.tts_provider}`);
      setStatus("done");
      await playVoiceAudio({
        audioBase64: result.tts_audio_base64,
        mimeType: result.tts_mime_type,
        onStart: () => setSpeechStatus("playing"),
        onEnd: () => setSpeechStatus("done"),
      });
      if (autoContinueRef.current) {
        setTimeout(() => handleStart(), 250);
      }
    } catch (voiceError) {
      setStatus("error");
      setSpeechStatus("error");
      setError(voiceError.message);
    }
  }

  function resetOutput() {
    setError("");
    setTranscript("");
    setAssistantText("");
    setIntent("none");
    setProvider("server");
    setSpeechStatus("idle");
  }

  return (
    <section className="workspace voice-workspace">
      <section className="control-panel">
        <div className="brand-row">
          <div>
            <p className="eyebrow">Server Voice</p>
            <h2>Microphone</h2>
          </div>
          <span className={`status status-${status}`}>{status}</span>
        </div>

        <VoiceControls
          autoContinue={autoContinue}
          intent={intent}
          isBusy={isBusy}
          isRecording={isRecording}
          language={language}
          languages={LANGUAGES}
          onAutoContinueChange={setAutoContinue}
          onLanguageChange={setLanguage}
          onStart={handleStart}
          onStop={handleStop}
          provider={provider}
          speechStatus={speechStatus}
          status={status}
        />

        {error ? <p className="error">{error}</p> : null}
      </section>

      <section className="voice-panel" aria-live="polite">
        <div className="response-header">
          <div>
            <p className="eyebrow">LLM Response</p>
            <h2>Assistant Response</h2>
          </div>
        </div>

        <div className="voice-output">
          <OutputBlock label="Transcript" value={transcript || "No transcript yet."} />
          <OutputBlock label="Response" value={assistantText || "Response will appear here."} />
        </div>
      </section>
    </section>
  );
}

export default VoicePage;
