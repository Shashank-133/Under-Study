import { useEffect, useState } from "react";
import "./App.css";

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
  { value: "ta", label: "Tamil" },
  { value: "te", label: "Telugu" },
];

const LANG_STORAGE_KEY = "understudy_language";
const API_URL = import.meta.env.VITE_API_URL || "";

function loadLanguage() {
  try {
    return localStorage.getItem(LANG_STORAGE_KEY) || "en";
  } catch {
    return "en";
  }
}

function InitialsBadge({ name }) {
  const initials = (name || "?")
    .split(" ")
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  return <div className="badge">{initials}</div>;
}

function ConfidenceBar({ value }) {
  const pct = Math.round((value || 0) * 100);
  return (
    <div className="confidence">
      <div className="confidence-track">
        <div className="confidence-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="confidence-label">{pct}% match</span>
    </div>
  );
}

function MemoryCard({ data }) {
  const top = data.similar_incidents?.[0];
  const person = data.ask_person || top?.resolved_by || "Unknown";

  return (
    <div className="memory-card">
      <div className="stamp">Match found</div>
      <h3 className="card-title">{top?.title || "Team memory result"}</h3>
      <div className="card-meta">
        {top?.id || "no-id"}
        {top?.pr_url ? (
          <>
            {" · "}
            <a href={top.pr_url} target="_blank" rel="noreferrer">
              View PR
            </a>
          </>
        ) : null}
      </div>
      <p className="card-body">{data.answer}</p>
      {top?.fix_summary ? <pre className="code-block">{top.fix_summary}</pre> : null}
      <div className="card-footer">
        <div className="person-row">
          <InitialsBadge name={person} />
          <div>
            <div className="person-name">{person}</div>
            <div className="person-tag">Suggested — not notified</div>
          </div>
        </div>
        <ConfidenceBar value={data.confidence} />
      </div>

      {data.similar_incidents?.length > 1 ? (
        <ul className="similar-list">
          {data.similar_incidents.slice(1).map((inc) => (
            <li key={inc.id}>
              <strong>{inc.title}</strong>
              <span>{Math.round(inc.similarity_score * 100)}%</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="empty-state">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M3 7l1.5-3h15L21 7M3 7v12a1 1 0 001 1h16a1 1 0 001-1V7M3 7h18M9 12h6"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <p>No record pulled yet.</p>
      <span>Submit an error to search your team&apos;s memory.</span>
    </div>
  );
}

function ErrorState({ message }) {
  return (
    <div className="empty-state error-state">
      <p>Could not reach Understudy</p>
      <span>{message}</span>
    </div>
  );
}

function ChatScreen({ initialError = "", onConsumedInitial }) {
  const [errorText, setErrorText] = useState(initialError);
  const [language, setLanguage] = useState(loadLanguage);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (initialError) {
      setErrorText(initialError);
      onConsumedInitial?.();
    }
  }, [initialError, onConsumedInitial]);

  useEffect(() => {
    try {
      localStorage.setItem(LANG_STORAGE_KEY, language);
    } catch {
      // ignore
    }
  }, [language]);

  async function handleAsk() {
    if (!errorText.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ error: errorText, language }),
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(
        e.message ||
          "Backend unreachable. Start it with: uvicorn app.main:app --reload --port 8000"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="main-grid">
      <div className="panel">
        <label className="panel-label" htmlFor="error-input">
          Paste your error or stack trace
        </label>
        <textarea
          id="error-input"
          className="input-mono"
          placeholder={
            "TypeError: Cannot read property 'map' of undefined\n    at Dashboard.jsx:24"
          }
          value={errorText}
          onChange={(e) => setErrorText(e.target.value)}
          disabled={loading}
        />
        <div className="controls-row">
          <div className="field">
            <label htmlFor="lang-select">Response language</label>
            <select
              id="lang-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={loading}
            >
              {LANGUAGES.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>
          <button
            className="btn-primary"
            onClick={handleAsk}
            disabled={loading || !errorText.trim()}
          >
            {loading ? "Searching…" : "Ask Understudy"}
          </button>
        </div>
      </div>

      <div className="panel result-panel">
        {loading ? (
          <div className="empty-state">
            <p>Searching team memory…</p>
          </div>
        ) : error ? (
          <ErrorState message={error} />
        ) : result ? (
          <MemoryCard data={result} />
        ) : (
          <EmptyState />
        )}
      </div>
    </div>
  );
}

function IngestionScreen({ onGoToChat }) {
  const [incidentText, setIncidentText] = useState("");
  const [ledger, setLedger] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleIngest() {
    if (!incidentText.trim()) return;
    setLoading(true);
    setStatus(null);
    const preview = incidentText.trim().slice(0, 90);
    try {
      const res = await fetch(`${API_URL}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw: incidentText }),
      });
      if (!res.ok) throw new Error(`Ingest failed (${res.status})`);
      const data = await res.json();
      setStatus(data.message || "Added to team memory.");
      setLedger((prev) => [
        {
          id: data.id || Date.now(),
          text: preview,
          time: new Date().toLocaleString(),
          raw: incidentText.trim(),
        },
        ...prev,
      ]);
      setIncidentText("");
    } catch (e) {
      setStatus(
        e.message ||
          "Could not reach POST /ingest. Is the backend running on port 8000?"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ingest-layout">
      <p className="ingest-intro">
        Add a new incident to team memory, then query the same error on the Chat screen.
      </p>
      <div className="panel">
        <label className="panel-label" htmlFor="incident-input">
          New incident — raw error or bug report
        </label>
        <textarea
          id="incident-input"
          className="input-mono"
          placeholder="Paste a stack trace or bug report to ingest…"
          value={incidentText}
          onChange={(e) => setIncidentText(e.target.value)}
          disabled={loading}
        />
        <button
          className="btn-primary"
          onClick={handleIngest}
          disabled={loading || !incidentText.trim()}
        >
          {loading ? "Ingesting…" : "Ingest incident"}
        </button>
        {status && <p className="status-line">{status}</p>}
      </div>

      <div className="ledger">
        <div className="ledger-heading">Recently ingested</div>
        {ledger.length === 0 ? (
          <p className="ledger-empty">Nothing ingested yet this session.</p>
        ) : (
          ledger.map((row) => (
            <div className="ledger-row" key={row.id}>
              <span className="ledger-text">{row.text}</span>
              <span className="ledger-actions">
                <button
                  type="button"
                  className="btn-link"
                  onClick={() => onGoToChat(row.raw)}
                >
                  Try in Chat →
                </button>
                <span className="ledger-time">{row.time}</span>
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState("chat");
  const [pendingError, setPendingError] = useState("");

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1 className="wordmark">Understudy</h1>
          <p className="tagline">AI pair-debugger with institutional memory</p>
        </div>
        <nav className="tab-nav">
          <button
            className={tab === "chat" ? "tab tab-active" : "tab"}
            onClick={() => setTab("chat")}
          >
            Chat
          </button>
          <button
            className={tab === "ingest" ? "tab tab-active" : "tab"}
            onClick={() => setTab("ingest")}
          >
            Ingestion demo
          </button>
        </nav>
      </header>

      {tab === "chat" ? (
        <ChatScreen
          initialError={pendingError}
          onConsumedInitial={() => setPendingError("")}
        />
      ) : (
        <IngestionScreen
          onGoToChat={(text) => {
            setPendingError(text);
            setTab("chat");
          }}
        />
      )}

      <footer className="app-footer">Understudy — HackHazards &apos;26</footer>
    </div>
  );
}
