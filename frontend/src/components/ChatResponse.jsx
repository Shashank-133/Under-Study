import ConfidenceBar from "./ConfidenceBar.jsx";
import SimilarIncidentsList from "./SimilarIncidentsList.jsx";
import { formatAnswerText } from "../utils/formatAnswer.js";

function FormattedAnswer({ text }) {
  const parts = formatAnswerText(text);

  return (
    <p className="answer">
      {parts.map((part) =>
        part.type === "code" ? (
          <code key={part.key} className="inline-code">
            {part.value}
          </code>
        ) : (
          <span key={part.key}>{part.value}</span>
        )
      )}
    </p>
  );
}

export default function ChatResponse({ response, fetchError, loading }) {
  return (
    <section className="response-panel" aria-live="polite">
      <h2>Response</h2>

      {fetchError && (
        <div className="error-box" role="alert">
          <strong>Could not reach Understudy</strong>
          <p>{fetchError}</p>
          <p className="error-hint">Make sure the backend is running: uvicorn app.main:app --reload --port 8000</p>
        </div>
      )}

      {loading && (
        <div className="loading-state">
          <div className="spinner" aria-hidden="true" />
          <p>Searching your team&apos;s institutional memory…</p>
        </div>
      )}

      {!fetchError && !response && !loading && (
        <p className="placeholder">Submit an error to see what your team remembers.</p>
      )}

      {response && !loading && (
        <div className="response-content">
          <FormattedAnswer text={response.answer} />
          <ConfidenceBar confidence={response.confidence} />

          {response.ask_person && (
            <p className="ask-person">
              Ask: <strong>{response.ask_person}</strong>
            </p>
          )}

          <SimilarIncidentsList incidents={response.similar_incidents} />
        </div>
      )}
    </section>
  );
}
