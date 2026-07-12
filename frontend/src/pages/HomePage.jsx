import { useCallback, useEffect, useState } from "react";
import ChatInput from "../components/ChatInput.jsx";
import ChatResponse from "../components/ChatResponse.jsx";
import { queryIncident } from "../utils/api.js";
import { LANGUAGE_STORAGE_KEY } from "../constants/languages.js";

function loadLanguage() {
  try {
    return localStorage.getItem(LANGUAGE_STORAGE_KEY) || "en";
  } catch {
    return "en";
  }
}

export default function HomePage({ initialErrorText = "", onConsumeInitialError }) {
  const [errorText, setErrorText] = useState(initialErrorText);
  const [language, setLanguage] = useState(loadLanguage);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [fetchError, setFetchError] = useState(null);

  useEffect(() => {
    if (initialErrorText) {
      setErrorText(initialErrorText);
      onConsumeInitialError?.();
    }
  }, [initialErrorText, onConsumeInitialError]);

  useEffect(() => {
    try {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    } catch {
      // ignore
    }
  }, [language]);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      if (!errorText.trim()) return;

      setLoading(true);
      setFetchError(null);
      setResponse(null);

      try {
        const data = await queryIncident(errorText, language);
        setResponse(data);
      } catch (err) {
        setFetchError(
          err.message || "Failed to reach backend. Is it running on port 8000?"
        );
      } finally {
        setLoading(false);
      }
    },
    [errorText, language]
  );

  return (
    <div className="page home-page">
      <p className="page-intro">
        Paste a bug or stack trace. Understudy searches what your team has fixed before.
      </p>

      <div className="chat-layout">
        <ChatInput
          errorText={errorText}
          onErrorTextChange={setErrorText}
          language={language}
          onLanguageChange={setLanguage}
          onSubmit={handleSubmit}
          loading={loading}
        />
        <ChatResponse response={response} fetchError={fetchError} loading={loading} />
      </div>
    </div>
  );
}
