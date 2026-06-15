export function buildAudioDataUrl(audioBase64, mimeType) {
  if (!audioBase64) {
    throw new Error("TTS audio is missing from server response.");
  }
  return `data:${mimeType || "audio/wav"};base64,${audioBase64}`;
}

export function playVoiceAudio({ audioBase64, mimeType, onStart, onEnd }) {
  const audio = new Audio(buildAudioDataUrl(audioBase64, mimeType));
  return new Promise((resolve, reject) => {
    audio.onplay = () => onStart?.();
    audio.onended = () => {
      onEnd?.();
      resolve();
    };
    audio.onerror = () => reject(new Error("TTS audio playback failed."));
    audio.play().catch(reject);
  });
}
