import { useState } from "react";
import "./App.css";

const LANGUAGES = ["English", "Hindi", "Tamil", "Telugu"];

const DEMO_MATCH = {
  title: "Cannot read property 'map' of undefined",
  file: "Dashboard.jsx:24",
  date: "March 14, 2026",
  rootCause:
    "A list was rendered before the async fetch resolved, so the items prop was still undefined on first render.",
  fix: "if (!items) return null;\n\nitems.map((item) => (\n  <Row key={item.id} data={item} />\n));",
  person: "Priya Sharma",
  confidence: 91,
};

const DEMO_LEDGER = [
  {
    id: 1,
    text: "TypeError: Cannot read property 'map' of undefined",
    time: "Jul 11, 2026 · 8:45 PM",
  },
  {
    id: 2,
    text: "UnhandledPromiseRejection: fetch failed — ECONNRESET",
    time: "Jul 10, 2026 · 6:12 PM",
  },
];

function InitialsBadge({ name }) {
  const initials = name
    .split(" ")
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  return <div className="badge">{initials}</div>;
}

function ConfidenceBar({ value }) {
  return (
    <div className="confidence">
      <div className="confidence-track">
        <div className="confidence-fill" style={{ width: `${value}%` }} />
      </div>
      <span className="confidence-label">{value}% match</span>
    </div>
  );
}

function MemoryCard({ match }) {
  return (
    <div className="memory-card">
      <div className="stamp">Match found</div>
      <h3 className="card-title">{match.title}</h3>
      <div className="card-meta">
        {match.file} &nbsp;·&nbsp; {match.date}
      </div>
      <p className="card-body">{match.rootCause}</p>
      <pre className="code-block">{match.fix}</pre>
      <div className="card-footer">
        <div className="person-row">
          <InitialsBadge name={match.person} />
          <div>
            <div className="person-name">{match.person}</div>
            <div className="person-tag">Suggested — not notified</div>
          </div>
        </div>
        <ConfidenceBar value={match.confidence} />
      </div>
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
      <span>Submit an error to search your team's memory.</span>
    </div>
  );
}

function ChatScreen() {
  const [errorText, setErrorText] = useState("");
  const [language, setLanguage] = useState("English");
  const [loading, setLoading] = useState(false);
  const [match, setMatch] = useState(null);

  async function handleAsk() {
    if (!errorText.trim()) return;
    setLoading(true);
    try {
      const res = await fetch("/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ error: errorText, language }),
      });
      if (!res.ok) throw new Error("query failed");
      const data = await res.json();
      setMatch(data);
    } catch (e) {
      setMatch(DEMO_MATCH);
    }
    setLoading(false);
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
          placeholder={"TypeError: Cannot read property 'map' of undefined\n    at Dashboard.jsx:24"}
          value={errorText}
          onChange={(e) => setErrorText(e.target.value)}
        />
        <div className="controls-row">
          <div className="field">
            <label htmlFor="lang-select">Response language</label>
            <select
              id="lang-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {LANGUAGES.map((l) => (
                <option key={l}>{l}</option>
              ))}
            </select>
          </div>
          <button className="btn-primary" onClick={handleAsk} disabled={loading}>
            {loading ? "Searching…" : "Ask Understudy"}
          </button>
        </div>
      </div>

      <div className="panel result-panel">
        {match ? <MemoryCard match={match} /> : <EmptyState />}
      </div>
    </div>
  );
}

function IngestionScreen() {
  const [incidentText, setIncidentText] = useState("");
  const [ledger, setLedger] = useState(DEMO_LEDGER);
  const [status, setStatus] = useState(null);

  async function handleIngest() {
    if (!incidentText.trim()) return;
    const entry = {
      id: Date.now(),
      text: incidentText.trim().slice(0, 90),
      time: new Date().toLocaleString(),
    };
    try {
      const res = await fetch("/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw: incidentText }),
      });
      if (!res.ok) throw new Error("ingest failed");
      setStatus("Added to team memory.");
    } catch (e) {
      setStatus("Saved locally — backend ingestion not connected yet.");
    }
    setLedger([entry, ...ledger]);
    setIncidentText("");
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
        />
        <button className="btn-primary" onClick={handleIngest}>
          Ingest incident
        </button>
        {status && <p className="status-line">{status}</p>}
      </div>

      <div className="ledger">
        <div className="ledger-heading">Recently ingested</div>
        {ledger.map((row) => (
          <div className="ledger-row" key={row.id}>
            <span className="ledger-text">{row.text}</span>
            <span className="ledger-time">{row.time}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState("chat");

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1 className="wordmark">Understudy</h1>
          <p className="tagline">
            The AI pair-debugger that remembers your team's <em>mistakes</em>.
          </p>
          <span className="tag-pill">HackHazards '26 · Dev Tools &amp; Infrastructure</span>
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

      {tab === "chat" ? <ChatScreen /> : <IngestionScreen />}

      <footer className="app-footer">Person 1 · Frontend · Understudy — HackHazards '26</footer>
    </div>
  );
}
