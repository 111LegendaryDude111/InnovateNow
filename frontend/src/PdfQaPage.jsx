import { useState } from "react";
import { askPdfQuestion, ingestPdfFiles } from "./api.js";

function PdfQaPage() {
  const [files, setFiles] = useState([]);
  const [session, setSession] = useState(null);
  const [question, setQuestion] = useState("What are the key obligations?");
  const [topK, setTopK] = useState(4);
  const [answer, setAnswer] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const isUploading = status === "uploading";
  const isAsking = status === "asking";

  async function handleUpload(event) {
    event.preventDefault();
    setError("");
    setAnswer(null);
    setStatus("uploading");

    try {
      const result = await ingestPdfFiles(files);
      setSession(result);
      setStatus("done");
    } catch (uploadError) {
      setStatus("error");
      setError(uploadError.message);
    }
  }

  async function handleAsk(event) {
    event.preventDefault();
    if (!session) return;
    setError("");
    setStatus("asking");

    try {
      const result = await askPdfQuestion({
        sessionId: session.session_id,
        question,
        topK,
      });
      setAnswer(result);
      setStatus("done");
    } catch (askError) {
      setStatus("error");
      setError(askError.message);
    }
  }

  return (
    <section className="workspace">
      <form className="control-panel" onSubmit={handleUpload}>
        <div className="brand-row">
          <div>
            <p className="eyebrow">PDF Q&A</p>
            <h2>Documents</h2>
          </div>
          <span className={`status status-${status}`}>{status}</span>
        </div>

        <label className="field" htmlFor="pdf-files">
          <span>PDF files</span>
          <input
            accept="application/pdf,.pdf"
            id="pdf-files"
            multiple
            onChange={(event) => setFiles([...event.target.files])}
            type="file"
          />
        </label>

        {files.length ? <SelectedFiles files={files} /> : null}

        <button
          className="primary-action"
          disabled={!files.length || isUploading}
          type="submit"
        >
          {isUploading ? "Processing..." : "Upload"}
        </button>

        {session ? <ProcessedDocuments session={session} /> : null}
        {error ? <p className="error">{error}</p> : null}
      </form>

      <section className="pdf-panel" aria-live="polite">
        <form className="pdf-question" onSubmit={handleAsk}>
          <div className="brand-row">
            <div>
              <p className="eyebrow">Question</p>
              <h2>Answer From PDFs</h2>
            </div>
            <label htmlFor="pdf-top-k">
              <span>Top K</span>
              <input
                id="pdf-top-k"
                max="8"
                min="1"
                onChange={(event) => setTopK(Number(event.target.value))}
                type="number"
                value={topK}
              />
            </label>
          </div>

          <textarea
            onChange={(event) => setQuestion(event.target.value)}
            rows={4}
            value={question}
          />
          <button
            className="primary-action"
            disabled={!session || isAsking}
            type="submit"
          >
            {isAsking ? "Asking..." : "Ask"}
          </button>
        </form>

        <div className="pdf-answer">
          <p>{answer?.answer || "Answer will appear here."}</p>
          {answer ? <SourceList title="Sources" items={answer.sources} /> : null}
          {answer ? (
            <SourceList title="Retrieved" items={answer.retrieved_chunks} />
          ) : null}
        </div>
      </section>
    </section>
  );
}

function SelectedFiles({ files }) {
  return (
    <ul className="pdf-list">
      {files.map((file) => (
        <li key={`${file.name}-${file.size}`}>
          <span>{file.name}</span>
          <strong>{Math.ceil(file.size / 1024)} KB</strong>
        </li>
      ))}
    </ul>
  );
}

function ProcessedDocuments({ session }) {
  return (
    <section className="pdf-documents">
      <p className="eyebrow">Processed</p>
      <ul className="pdf-list">
        {session.documents.map((document) => (
          <li key={document.filename}>
            <span>{document.filename}</span>
            <strong>{document.chunk_count} chunks</strong>
          </li>
        ))}
      </ul>
    </section>
  );
}

function SourceList({ title, items }) {
  return (
    <section className="pdf-sources">
      <h3>{title}</h3>
      {items.length ? (
        <ol>
          {items.map((item) => (
            <li key={`${title}-${item.chunk_id}-${item.rank}`}>
              <strong>
                {item.filename}, page {item.page}, rank {item.rank}
              </strong>
              <span>{item.score.toFixed(3)}</span>
              <p>{item.snippet}</p>
            </li>
          ))}
        </ol>
      ) : (
        <p>No sources.</p>
      )}
    </section>
  );
}

export default PdfQaPage;
