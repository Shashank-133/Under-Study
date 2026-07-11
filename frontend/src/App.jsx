import { useCallback, useState } from "react";
import HomePage from "./pages/HomePage.jsx";
import IngestionDemoPage from "./pages/IngestionDemoPage.jsx";
import { getPendingQuery, setPendingQuery } from "./utils/storage.js";

const PAGES = {
  chat: "chat",
  ingest: "ingest",
};

export default function App() {
  const [page, setPage] = useState(PAGES.chat);
  const [prefillError, setPrefillError] = useState("");

  const navigateToChat = useCallback((text) => {
    const queryText = text || getPendingQuery();
    setPrefillError(queryText);
    setPage(PAGES.chat);
  }, []);

  const consumeInitialError = useCallback(() => {
    setPrefillError("");
    setPendingQuery("");
  }, []);

  return (
    <div className="app">
      <header className="header">
        <div className="header-top">
          <div>
            <h1>Understudy</h1>
            <p className="tagline">AI pair-debugger with institutional memory</p>
          </div>
          <nav className="nav" aria-label="Main">
            <button
              type="button"
              className={`nav-btn ${page === PAGES.chat ? "active" : ""}`}
              onClick={() => setPage(PAGES.chat)}
            >
              Chat
            </button>
            <button
              type="button"
              className={`nav-btn ${page === PAGES.ingest ? "active" : ""}`}
              onClick={() => setPage(PAGES.ingest)}
            >
              Ingestion Demo
            </button>
          </nav>
        </div>
      </header>

      <main className="main">
        {page === PAGES.chat ? (
          <HomePage
            initialErrorText={prefillError}
            onConsumeInitialError={consumeInitialError}
          />
        ) : (
          <IngestionDemoPage onNavigateToChat={navigateToChat} />
        )}
      </main>

      <footer className="footer">
        <span>Person 1 · Frontend</span>
        <span className="footer-sep">·</span>
        <span>Understudy Hackathon</span>
      </footer>
    </div>
  );
}
