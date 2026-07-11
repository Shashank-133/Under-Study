import LanguageToggle from "./LanguageToggle.jsx";

export default function ChatInput({
  errorText,
  onErrorTextChange,
  language,
  onLanguageChange,
  onSubmit,
  loading,
}) {
  return (
    <form className="query-form" onSubmit={onSubmit}>
      <label htmlFor="error-input">Paste your error or stack trace</label>
      <textarea
        id="error-input"
        value={errorText}
        onChange={(e) => onErrorTextChange(e.target.value)}
        placeholder={`TypeError: Cannot read property 'map' of undefined\nat Dashboard.jsx:24`}
        rows={6}
        disabled={loading}
      />

      <div className="controls">
        <LanguageToggle language={language} onLanguageChange={onLanguageChange} disabled={loading} />

        <button type="submit" className="btn-primary" disabled={loading || !errorText.trim()}>
          {loading ? "Searching team memory…" : "Ask Understudy"}
        </button>
      </div>
    </form>
  );
}
