import { useState } from "react";
import "./App.css";

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
  { value: "ta", label: "Tamil" },
  { value: "te", label: "Telugu" },
];

/** Dummy credentials for the demo video — not real auth. */
const DEMO_EMAIL = "demo@understudy.dev";
const DEMO_PASSWORD = "demo123";
const AUTH_KEY = "understudy_demo_auth";

function isLoggedIn() {
  try {
    return sessionStorage.getItem(AUTH_KEY) === "1";
  } catch {
    return false;
  }
}

function setLoggedIn(value) {
  try {
    if (value) sessionStorage.setItem(AUTH_KEY, "1");
    else sessionStorage.removeItem(AUTH_KEY);
  } catch {
    // ignore
  }
}

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

const API_URL = import.meta.env.VITE_API_URL || "";

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
  // API sends 0–1; demo fallback may send 0–100
  const pct = value > 1 ? Math.round(value) : Math.round((value || 0) * 100);
  return (
    <div className="confidence">
      <div className="confidence-track">
        <div className="confidence-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="confidence-label">{pct}% match</span>
    </div>
  );
}

function mapApiToCard(data) {
  const top = data.similar_incidents?.[0];
  if (!top && !data.answer) return null;

  return {
    title: top?.title || "No close match in team memory",
    file: top?.id || "—",
    date: top?.pr_url ? "View PR" : "No linked PR",
    prUrl: top?.pr_url || "",
    rootCause: data.answer || "No similar incidents found yet.",
    fix: top?.fix_summary || "Try pasting a fuller stack trace, or ingest this as a new incident.",
    person: data.ask_person || top?.resolved_by || "—",
    confidence: data.confidence ?? 0,
  };
}

function MemoryCard({ match }) {
  return (
    <div className="memory-card">
      <div className="stamp">{match.confidence > 0.12 ? "Match found" : "No match"}</div>
      <h3 className="card-title">{match.title}</h3>
      <div className="card-meta">
        {match.file}
        {match.prUrl ? (
          <>
            {" · "}
            <a href={match.prUrl} target="_blank" rel="noreferrer">
              {match.date}
            </a>
          </>
        ) : (
          <> &nbsp;·&nbsp; {match.date}</>
        )}
      </div>
      <p className="card-body">{match.rootCause}</p>
      <pre className="code-block">{match.fix}</pre>
      <div className="card-footer">
        <div className="person-row">
          <InitialsBadge name={match.person === "—" ? "?" : match.person} />
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
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);
  const [match, setMatch] = useState(null);
  const [error, setError] = useState(null);

  async function handleAsk() {
    if (!errorText.trim()) return;
    setLoading(true);
    setError(null);
    setMatch(null);
    try {
      const res = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ error: errorText, language }),
      });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(`API ${res.status}: ${detail.slice(0, 120)}`);
      }
      const data = await res.json();
      setMatch(mapApiToCard(data) || DEMO_MATCH);
    } catch (e) {
      setError(e.message || "Could not reach backend on port 8000.");
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
          <button className="btn-primary" onClick={handleAsk} disabled={loading || !errorText.trim()}>
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
          <div className="empty-state">
            <p>Could not reach Understudy</p>
            <span>{error}</span>
          </div>
        ) : match ? (
          <MemoryCard match={match} />
        ) : (
          <EmptyState />
        )}
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
      const res = await fetch(`${API_URL}/ingest`, {
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

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function fillDemo() {
    setEmail(DEMO_EMAIL);
    setPassword(DEMO_PASSWORD);
    setError("");
  }

  function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    window.setTimeout(() => {
      if (
        email.trim().toLowerCase() === DEMO_EMAIL &&
        password === DEMO_PASSWORD
      ) {
        setLoggedIn(true);
        onLogin();
      } else {
        setError("Invalid credentials. Use the demo account shown below.");
      }
      setLoading(false);
    }, 450);
  }

  return (
    <div className="login-page">
      <div className="login-shell">
        <header className="login-brand">
          <h1 className="wordmark">Understudy</h1>
          <p className="tagline">
            The AI pair-debugger that remembers your team&apos;s <em>mistakes</em>.
          </p>
          <span className="tag-pill">HackHazards &apos;26 · Demo login</span>
        </header>

        <form className="login-panel panel" onSubmit={handleSubmit}>
          <p className="login-heading">Sign in to team memory</p>

          <label className="panel-label" htmlFor="login-email">
            Email
          </label>
          <input
            id="login-email"
            className="login-input"
            type="email"
            autoComplete="username"
            placeholder={DEMO_EMAIL}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
          />

          <label className="panel-label" htmlFor="login-password">
            Password
          </label>
          <input
            id="login-password"
            className="login-input"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
          />

          {error ? (
            <p className="login-error" role="alert">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            className="btn-primary login-submit"
            disabled={loading || !email.trim() || !password}
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>

          <div className="demo-creds">
            <div className="demo-creds-label">Demo credentials</div>
            <code>
              {DEMO_EMAIL} / {DEMO_PASSWORD}
            </code>
            <button type="button" className="btn-link" onClick={fillDemo}>
              Fill demo account →
            </button>
          </div>
        </form>

        <p className="login-foot">Demo only — not real authentication</p>
      </div>
    </div>
  );
}

function MainApp({ onLogout }) {
  const [tab, setTab] = useState("chat");

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1 className="wordmark">Understudy</h1>
          <p className="tagline">
            The AI pair-debugger that remembers your team&apos;s <em>mistakes</em>.
          </p>
          <span className="tag-pill">HackHazards &apos;26 · Dev Tools &amp; Infrastructure</span>
        </div>
        <div className="header-actions">
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
          <button type="button" className="btn-logout" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </header>

      {tab === "chat" ? <ChatScreen /> : <IngestionScreen />}

      <footer className="app-footer">Understudy — HackHazards &apos;26</footer>
    </div>
  );
}

export default function App() {
  const [authed, setAuthed] = useState(isLoggedIn);

  function handleLogout() {
    setLoggedIn(false);
    setAuthed(false);
  }

  if (!authed) {
    return <LoginPage onLogin={() => setAuthed(true)} />;
  }

  return <MainApp onLogout={handleLogout} />;
}
