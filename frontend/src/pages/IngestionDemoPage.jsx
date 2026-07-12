import { useEffect, useState } from "react";
import { ingestIncident } from "../utils/api.js";
import { addIngestedIncident, getIngestedIncidents, setPendingQuery } from "../utils/storage.js";

export default function IngestionDemoPage({ onNavigateToChat }) {
  const [rawText, setRawText] = useState("");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    setRecent(getIngestedIncidents());
  }, []);

  async function handleIngest(e) {
    e.preventDefault();
    if (!rawText.trim()) return;

    setLoading(true);
    setToast(null);

    try {
      const result = await ingestIncident(rawText.trim());
      const updated = addIngestedIncident(result);
      setRecent(updated);
      setToast({
        type: "success",
        message: "Incident ingested into team memory (demo mode).",
      });
      setRawText("");
    } catch (err) {
      setToast({
        type: "error",
        message: err.message || "Ingestion failed. Try again.",
      });
    } finally {
      setLoading(false);
    }
  }

  function handleTryInChat(text) {
    setPendingQuery(text);
    onNavigateToChat(text);
  }

  return (
    <div className="page ingestion-page">
      <p className="page-intro">
        Demo: add a new incident to team memory, then query the same error on the Chat screen.
      </p>

      {toast && (
        <div className={`toast toast-${toast.type}`} role="status">
          {toast.message}
        </div>
      )}

      <form className="ingest-form" onSubmit={handleIngest}>
        <label htmlFor="ingest-input">New incident (raw error or bug report)</label>
        <textarea
          id="ingest-input"
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          placeholder="Paste a stack trace or bug description to ingest…"
          rows={8}
          disabled={loading}
        />
        <button type="submit" className="btn-primary" disabled={loading || !rawText.trim()}>
          {loading ? "Ingesting…" : "Ingest incident"}
        </button>
      </form>

      <section className="ingest-steps card">
        <h3>Demo flow</h3>
        <ol>
          <li>Paste a new error above and click <strong>Ingest incident</strong>.</li>
          <li>Wait for the success message — simulates the Render ingestion pipeline.</li>
          <li>Go to <strong>Chat</strong> and query the same error to see it surface.</li>
        </ol>
        <p className="note">
          Calls backend <code className="inline-code">POST /ingest</code> which extracts
          structure (Sarvam when keyed) and writes to Neo4j / runtime memory.
        </p>
      </section>

      {recent.length > 0 && (
        <section className="recent-ingestions card">
          <h3>Recently ingested (demo)</h3>
          <ul>
            {recent.slice(0, 5).map((item) => (
              <li key={item.id}>
                <p className="ingest-preview">
                  {item.raw_text.split("\n")[0].slice(0, 120)}
                  {item.raw_text.length > 120 ? "…" : ""}
                </p>
                <p className="meta">
                  {new Date(item.ingested_at).toLocaleString()}
                  {" · "}
                  <button
                    type="button"
                    className="btn-link"
                    onClick={() => handleTryInChat(item.raw_text)}
                  >
                    Try in Chat →
                  </button>
                </p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
