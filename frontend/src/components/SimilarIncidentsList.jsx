export default function SimilarIncidentsList({ incidents }) {
  if (!incidents?.length) return null;

  return (
    <div className="incidents">
      <h3>Similar past incidents</h3>
      <ul>
        {incidents.map((inc) => (
          <li key={inc.id}>
            <div className="incident-header">
              <strong>{inc.title}</strong>
              <span className="match-badge">{Math.round(inc.similarity_score * 100)}% match</span>
            </div>
            <p className="fix-summary">{inc.fix_summary}</p>
            <p className="meta">
              Fixed by {inc.resolved_by}
              {inc.pr_url ? (
                <>
                  {" · "}
                  <a href={inc.pr_url} target="_blank" rel="noreferrer">
                    View PR
                  </a>
                </>
              ) : null}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
