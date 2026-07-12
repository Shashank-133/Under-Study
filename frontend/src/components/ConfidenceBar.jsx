export default function ConfidenceBar({ confidence }) {
  const percent = Math.round((confidence ?? 0) * 100);

  return (
    <div className="confidence" role="meter" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100}>
      <span className="confidence-label">Confidence</span>
      <div className="confidence-bar">
        <div className="confidence-fill" style={{ width: `${percent}%` }} />
      </div>
      <span className="confidence-value">{percent}%</span>
    </div>
  );
}
