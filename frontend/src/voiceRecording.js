export const AUDIO_MIME_TYPES = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];

export function hasAudioRecording() {
  return "MediaRecorder" in window && Boolean(navigator.mediaDevices?.getUserMedia);
}

export function getSupportedAudioMimeType() {
  if (!("MediaRecorder" in window)) return "";
  return selectSupportedAudioMimeType((mimeType) => MediaRecorder.isTypeSupported(mimeType));
}

export function selectSupportedAudioMimeType(isTypeSupported, candidates = AUDIO_MIME_TYPES) {
  return candidates.find((mimeType) => isTypeSupported(mimeType)) ?? "";
}

export function createAudioBlob(chunks, mimeType) {
  return new Blob(chunks, { type: mimeType || chunks[0]?.type || "application/octet-stream" });
}

export function stopStream(stream) {
  stream?.getTracks().forEach((track) => track.stop());
}
