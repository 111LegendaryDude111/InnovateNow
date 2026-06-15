import { useState } from "react";
import { generateImage } from "./api.js";

const ASPECT_OPTIONS = [
  { id: "square", label: "1:1" },
  { id: "landscape", label: "3:2" },
  { id: "portrait", label: "2:3" },
];

const STYLE_OPTIONS = [
  { id: "photorealistic", label: "Photo" },
  { id: "product", label: "Product" },
  { id: "illustration", label: "Illustration" },
  { id: "minimal", label: "Minimal" },
  { id: "none", label: "None" },
];

function ImagePage() {
  const [prompt, setPrompt] = useState(
    "A premium reusable water bottle on a clean desk, morning light, crisp brand campaign composition",
  );
  const [aspectRatio, setAspectRatio] = useState("square");
  const [stylePreset, setStylePreset] = useState("product");
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [currentImage, setCurrentImage] = useState(null);
  const [history, setHistory] = useState([]);
  const isLoading = status === "loading";

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setStatus("loading");

    try {
      const result = await generateImage({ prompt, aspectRatio, stylePreset });
      const item = buildGalleryItem(result);
      setCurrentImage(item);
      setHistory((items) => [item, ...items].slice(0, 8));
      setStatus("done");
    } catch (imageError) {
      setStatus("error");
      setError(imageError.message);
    }
  }

  function handleDownload() {
    if (!currentImage) return;

    const link = document.createElement("a");
    link.href = currentImage.dataUrl;
    link.download = `creativecanvas-${currentImage.id}.png`;
    link.click();
  }

  return (
    <>
      <section className="workspace">
        <form className="control-panel" onSubmit={handleSubmit}>
          <div className="brand-row">
            <div>
              <p className="eyebrow">CreativeCanvas AI</p>
              <h2>Image Studio</h2>
            </div>
            <span className={`status status-${status}`}>{status}</span>
          </div>

          <label className="field" htmlFor="image-prompt">
            <span>Prompt</span>
            <textarea
              id="image-prompt"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              rows={8}
            />
          </label>

          <fieldset>
            <legend>Aspect</legend>
            <div className="segmented">
              {ASPECT_OPTIONS.map((option) => (
                <button
                  className={aspectRatio === option.id ? "selected" : ""}
                  key={option.id}
                  onClick={() => setAspectRatio(option.id)}
                  type="button"
                >
                  {option.label}
                </button>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend>Style</legend>
            <div className="style-grid">
              {STYLE_OPTIONS.map((option) => (
                <label key={option.id}>
                  <input
                    checked={stylePreset === option.id}
                    name="style"
                    onChange={() => setStylePreset(option.id)}
                    type="radio"
                  />
                  <span>{option.label}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <button className="primary-action" disabled={isLoading} type="submit">
            {isLoading ? "Generating..." : "Generate"}
          </button>
          {error ? <p className="error">{error}</p> : null}
        </form>

        <section className="canvas-panel" aria-live="polite">
          <div className="canvas-toolbar">
            <div>
              <p className="eyebrow">Output</p>
              <h2>{currentImage ? currentImage.size : "Awaiting image"}</h2>
            </div>
            <button
              className="secondary-action"
              disabled={!currentImage}
              onClick={handleDownload}
              type="button"
            >
              Download
            </button>
          </div>

          <div className={`image-stage ${currentImage ? "" : "empty-stage"}`}>
            {currentImage ? (
              <img alt={currentImage.prompt} src={currentImage.dataUrl} />
            ) : (
              <span>PNG preview</span>
            )}
          </div>
        </section>
      </section>

      <section className="history-strip" aria-label="Session history">
        {history.length ? (
          history.map((item) => (
            <button key={item.id} onClick={() => setCurrentImage(item)} type="button">
              <img alt={item.prompt} src={item.dataUrl} />
              <span>{item.aspectRatio}</span>
            </button>
          ))
        ) : (
          <p>No session images yet.</p>
        )}
      </section>
    </>
  );
}

function buildGalleryItem(result) {
  return {
    id: String(Date.now()),
    dataUrl: `data:${result.mime_type};base64,${result.image_base64}`,
    prompt: result.prompt,
    aspectRatio: result.aspect_ratio,
    stylePreset: result.style_preset,
    size: result.size,
  };
}

export default ImagePage;
