import { useState } from "react";

const STREAM_ENDPOINT = "http://127.0.0.1:8000/llm/stream";

function App() {
  const [prompt, setPrompt] = useState("Explain Python unit tests");
  const [system, setSystem] = useState("Be concise");
  const [answer, setAnswer] = useState("");
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  // Запускает POST-запрос и читает SSE stream через fetch.
  async function handleSubmit(event) {
    event.preventDefault();
    setAnswer("");
    setError("");
    setStatus("streaming");

    try {
      await streamAnswer({
        prompt,
        system,
        onChunk: (chunk) => setAnswer((current) => current + chunk),
      });
      setStatus("done");
    } catch (streamError) {
      setStatus("error");
      setError(streamError.message);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <form className="prompt-panel" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="prompt">Prompt</label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              rows={7}
            />
          </div>

          <div className="field">
            <label htmlFor="system">System</label>
            <input
              id="system"
              value={system}
              onChange={(event) => setSystem(event.target.value)}
            />
          </div>

          <button type="submit" disabled={status === "streaming"}>
            {status === "streaming" ? "Streaming..." : "Send"}
          </button>
        </form>

        <section className="response-panel" aria-live="polite">
          <div className="response-header">
            <h1>LLM Stream</h1>
            <span className={`status status-${status}`}>{status}</span>
          </div>
          <pre>{answer || "Response will appear here."}</pre>
          {error ? <p className="error">{error}</p> : null}
        </section>
      </section>
    </main>
  );
}

// Читает байты ответа и передает разобранные SSE events обработчику.
async function streamAnswer({ prompt, system, onChunk }) {
  const response = await fetch(STREAM_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, system }),
  });

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(message);
  }

  if (!response.body) {
    throw new Error("Streaming response body is unavailable");
  }

  const reader = response.body.getReader();
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

// Обрабатывает одно SSE-событие из backend stream.
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

// Возвращает понятный текст ошибки от FastAPI validation response.
async function readErrorMessage(response) {
  const payload = await response.json();
  return payload.detail;
}

export default App;
