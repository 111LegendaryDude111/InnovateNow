import { useState } from "react";
import ImagePage from "./ImagePage.jsx";
import PdfQaPage from "./PdfQaPage.jsx";
import StreamPage from "./StreamPage.jsx";
import VoicePage from "./VoicePage.jsx";

const PAGES = [
  { id: "stream", label: "LLM Stream", title: "Streaming Messages" },
  { id: "images", label: "Images", title: "CreativeCanvas AI" },
  { id: "voice", label: "Voice Assistant", title: "Voice Assistant" },
  { id: "pdf", label: "PDF Q&A", title: "PDF Q&A" },
];

function App() {
  const [activePage, setActivePage] = useState("stream");
  const pageTitle = PAGES.find((page) => page.id === activePage).title;

  return (
    <main className="app-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Task Learn</p>
          <h1>{pageTitle}</h1>
        </div>
        <nav className="page-tabs" aria-label="App pages">
          {PAGES.map((page) => (
            <button
              className={activePage === page.id ? "selected" : ""}
              key={page.id}
              onClick={() => setActivePage(page.id)}
              type="button"
            >
              {page.label}
            </button>
          ))}
        </nav>
      </header>

      {activePage === "stream" ? <StreamPage /> : null}
      {activePage === "images" ? <ImagePage /> : null}
      {activePage === "voice" ? <VoicePage /> : null}
      {activePage === "pdf" ? <PdfQaPage /> : null}
    </main>
  );
}

export default App;
