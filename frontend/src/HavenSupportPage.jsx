import { useState } from "react";
import { askHavenSupport } from "./api.js";

const SAMPLE_MESSAGES = [
  "How do I pair a new Haven Cam?",
  "What is included in Haven Secure?",
  "I can't log in and need a password reset",
];

function HavenSupportPage() {
  const [message, setMessage] = useState(SAMPLE_MESSAGES[0]);
  const [channel, setChannel] = useState("help_center");
  const [response, setResponse] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const isLoading = status === "loading";

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus("loading");
    setError("");

    try {
      const result = await askHavenSupport({ message, channel });
      setResponse(result);
      setStatus("done");
    } catch (supportError) {
      setStatus("error");
      setError(supportError.message);
    }
  }

  return (
    <section className="workspace">
      <form className="control-panel" onSubmit={handleSubmit}>
        <div className="brand-row">
          <div>
            <p className="eyebrow">Haven</p>
            <h2>Support Bot</h2>
          </div>
          <span className={`status status-${status}`}>{status}</span>
        </div>

        <fieldset>
          <legend>Surface</legend>
          <div className="segmented support-segments">
            <button
              className={channel === "help_center" ? "selected" : ""}
              onClick={() => setChannel("help_center")}
              type="button"
            >
              Help Center
            </button>
            <button
              className={channel === "in_app" ? "selected" : ""}
              onClick={() => setChannel("in_app")}
              type="button"
            >
              In App
            </button>
          </div>
        </fieldset>

        <label className="field" htmlFor="haven-message">
          <span>Customer message</span>
          <textarea
            id="haven-message"
            onChange={(event) => setMessage(event.target.value)}
            rows={7}
            value={message}
          />
        </label>

        <div className="support-examples">
          {SAMPLE_MESSAGES.map((sample) => (
            <button key={sample} onClick={() => setMessage(sample)} type="button">
              {sample}
            </button>
          ))}
        </div>

        <button className="primary-action" disabled={isLoading} type="submit">
          {isLoading ? "Checking..." : "Send"}
        </button>

        {error ? <p className="error">{error}</p> : null}
      </form>

      <section className="support-panel" aria-live="polite">
        <div className="support-answer">
          <div className="brand-row">
            <div>
              <p className="eyebrow">{response?.intent || "Intent"}</p>
              <h2>{response?.action || "Waiting"}</h2>
            </div>
            <span className={`support-action action-${response?.action || "idle"}`}>
              {response?.channel || channel}
            </span>
          </div>

          <p>{response?.answer || "Response will appear here."}</p>

          {response ? <SupportList title="Next steps" items={response.next_steps} /> : null}
          {response?.sources.length ? (
            <SupportList
              title="Sources"
              items={response.sources.map((source) => source.title)}
            />
          ) : null}
          {response?.handoff ? <Handoff payload={response.handoff} /> : null}
        </div>
      </section>
    </section>
  );
}

function SupportList({ title, items }) {
  return (
    <section className="support-list">
      <h3>{title}</h3>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function Handoff({ payload }) {
  return (
    <section className="support-handoff">
      <h3>Handoff</h3>
      <dl>
        <dt>Status</dt>
        <dd>{payload.status}</dd>
        <dt>Reason</dt>
        <dd>{payload.reason}</dd>
        <dt>Next</dt>
        <dd>{payload.next_step}</dd>
      </dl>
    </section>
  );
}

export default HavenSupportPage;
