export function getSpeechRecognitionConstructor() {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

export function hasSpeechSynthesis() {
  return "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
}

// Запускает browser TTS и сообщает UI о статусе озвучивания.
export function speakResponse(text, speechLang, setSpeechStatus, setError) {
  window.speechSynthesis.cancel();
  const utterance = new window.SpeechSynthesisUtterance(text);
  utterance.lang = speechLang;
  utterance.onstart = () => setSpeechStatus("speaking");
  utterance.onend = () => setSpeechStatus("done");
  utterance.onerror = () => {
    setSpeechStatus("error");
    setError("Speech synthesis failed.");
  };
  window.speechSynthesis.speak(utterance);
}

export function describeRecognitionError(error) {
  const messages = {
    "audio-capture": "Microphone is unavailable.",
    network:
      "Browser speech recognition service is unavailable. Check internet access and browser speech-service blocking, or switch this MVP to cloud/local STT for reliable recognition.",
    "no-speech": "No speech was recognized. Try again.",
    "not-allowed": "Microphone permission denied.",
    "service-not-allowed": "Speech Recognition service is not allowed.",
  };
  return messages[error] ?? `Speech Recognition failed: ${error || "unknown error"}.`;
}
