const IMAGE_ENDPOINT = "http://127.0.0.1:8000/images/generate";
const STREAM_ENDPOINT = "http://127.0.0.1:8000/llm/stream";
const VOICE_ENDPOINT = "http://127.0.0.1:8000/voice/respond";

export async function generateImage({ prompt, aspectRatio, stylePreset }) {
  const response = await fetch(IMAGE_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt,
      aspect_ratio: aspectRatio,
      style_preset: stylePreset,
    }),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json();
}

export async function streamAnswer({ prompt, system, onChunk }) {
  const response = await fetch(STREAM_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, system }),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  if (!response.body) {
    throw new Error("Streaming response body is unavailable");
  }

  await readStreamEvents(response.body, onChunk);
}

export async function requestVoiceResponse({ audioBlob, language }) {
  const response = await fetch(`${VOICE_ENDPOINT}?language=${encodeURIComponent(language)}`, {
    method: "POST",
    headers: { "Content-Type": audioBlob.type || "application/octet-stream" },
    body: audioBlob,
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json();
}

// Читает SSE chunks из fetch stream и передает delta-события UI.
async function readStreamEvents(body, onChunk) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop();

    for (const rawEvent of events) {
      handleStreamEvent(rawEvent, onChunk);
    }
  }
}

// Обрабатывает одно SSE-событие от backend stream.
function handleStreamEvent(rawEvent, onChunk) {
  const dataLine = rawEvent.split("\n").find((line) => line.startsWith("data: "));
  if (!dataLine) return;

  const payload = JSON.parse(dataLine.slice(6));
  if (payload.type === "delta") {
    onChunk(payload.content);
  }
  if (payload.type === "error") {
    throw new Error(payload.error);
  }
}

async function readErrorMessage(response) {
  const payload = await response.json();
  return payload.detail;
}
