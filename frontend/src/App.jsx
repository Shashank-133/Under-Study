import { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "";

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
  { value: "ta", label: "Tamil" },
  { value: "te", label: "Telugu" },
];

export default function App() {
  const [errorText, setErrorText] = useState("");
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [fetchError, setFetchError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!errorText.trim()) return;

    setLoading(true);
    setFetchError(null);
    setResponse(null);

    try {
      const res = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ error: errorText, language }),
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setFetchError(err.message || "Failed to reach backend. Is it running on port 8000?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Understudy</h1>
        <p className="tagline">AI pair-debugger with institutional memory</p>
      </header>

      <main className="main">
        <form className="query-form" onSubmit={handleSubmit}>
          <label htmlFor="error-input">Paste your error or stack trace</label>
          <textarea
            id="error-input"
            value={errorText}
            onChange={(e) => setErrorText(e.target.value)}
            placeholder="TypeError: Cannot read property 'map' of undefined&#10;at Dashboard.jsx:24"
            rows={6}
          />

          <div className="controls">
            <label htmlFor="language-select">Response language</label>
            <select
              id="language-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {LANGUAGES.map((lang) => (
                <option key={lang.value} value={lang.value}>
                  {lang.label}
                </option>
              ))}
            </select>

            <button type="submit" disabled={loading || !errorText.trim()}>
              {loading ? "Searching team memory…" : "Ask Understudy"}
            </button>
          </div>
        </form>

        <section className="response-panel">
          <h2>Response</h2>

          {fetchError && <div className="error-box">{fetchError}</div>}

          {!fetchError && !response && !loading && (
            <p className="placeholder">Submit an error to see what your team remembers.</p>
          )}

          {response && (
            <div className="response-content">
              <p className="answer">{response.answer}</p>

              <div className="confidence">
                <span>Confidence</span>
                <div className="confidence-bar">
                  <div
                    className="confidence-fill"
                    style={{ width: `${Math.round(response.confidence * 100)}%` }}
                  />
                </div>
                <span>{Math.round(response.confidence * 100)}%</span>
              </div>

              {response.ask_person && (
                <p className="ask-person">
                  Ask: <strong>{response.ask_person}</strong>
                </p>
              )}

              {response.similar_incidents?.length > 0 && (
                <div className="incidents">
                  <h3>Similar past incidents</h3>
                  <ul>
                    {response.similar_incidents.map((inc) => (
                      <li key={inc.id}>
                        <strong>{inc.title}</strong> ({Math.round(inc.similarity_score * 100)}% match)
                        <p>{inc.fix_summary}</p>
                        <p className="meta">
                          Fixed by {inc.resolved_by} ·{" "}
                          <a href={inc.pr_url} target="_blank" rel="noreferrer">
                            PR
                          </a>
                        </p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
