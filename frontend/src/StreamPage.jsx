import { useState } from "react";
import { streamAnswer } from "./api.js";

function StreamPage() {
  const [prompt, setPrompt] = useState("Explain Python unit tests");
  const [system, setSystem] = useState("Be concise");
  const [answer, setAnswer] = useState("");
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const isStreaming = status === "streaming";

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
    <section className="workspace">
      <form className="control-panel" onSubmit={handleSubmit}>
        <div className="brand-row">
          <div>
            <p className="eyebrow">OpenRouter</p>
            <h2>Message Stream</h2>
          </div>
          <span className={`status status-${status}`}>{status}</span>
        </div>

        <label className="field" htmlFor="stream-prompt">
          <span>Prompt</span>
          <textarea
            id="stream-prompt"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            rows={7}
          />
        </label>

        <label className="field" htmlFor="system">
          <span>System</span>
          <input
            id="system"
            value={system}
            onChange={(event) => setSystem(event.target.value)}
          />
        </label>

        <button className="primary-action" disabled={isStreaming} type="submit">
          {isStreaming ? "Streaming..." : "Send"}
        </button>
      </form>

      <section className="response-panel" aria-live="polite">
        <div className="response-header">
          <div>
            <p className="eyebrow">Response</p>
            <h2>Live Output</h2>
          </div>
        </div>
        <pre>{answer || "Response will appear here."}</pre>
        {error ? <p className="error">{error}</p> : null}
      </section>
    </section>
  );
}

export default StreamPage;
