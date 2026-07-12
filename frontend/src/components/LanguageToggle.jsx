import { LANGUAGES } from "../constants/languages.js";

export default function LanguageToggle({ language, onLanguageChange, disabled = false }) {
  return (
    <div className="language-toggle">
      <label htmlFor="language-select">Response language</label>
      <select
        id="language-select"
        value={language}
        onChange={(e) => onLanguageChange(e.target.value)}
        disabled={disabled}
        aria-label="Response language"
      >
        {LANGUAGES.map((lang) => (
          <option key={lang.value} value={lang.value}>
            {lang.label}
          </option>
        ))}
      </select>
    </div>
  );
}
