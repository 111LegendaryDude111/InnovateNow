import { useState } from "react";
import ImagePage from "./ImagePage.jsx";
import StreamPage from "./StreamPage.jsx";

const PAGES = [
  { id: "stream", label: "LLM Stream" },
  { id: "images", label: "Images" },
];

function App() {
  const [activePage, setActivePage] = useState("stream");

  return (
    <main className="app-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Task Learn</p>
          <h1>{activePage === "stream" ? "Streaming Messages" : "CreativeCanvas AI"}</h1>
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

      {activePage === "stream" ? <StreamPage /> : <ImagePage />}
    </main>
  );
}

export default App;
