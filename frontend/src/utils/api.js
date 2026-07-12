const API_URL = import.meta.env.VITE_API_URL || "";

export async function queryIncident(error, language = "en") {
  const res = await fetch(`${API_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ error, language }),
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}

export async function ingestIncident(rawText) {
  const res = await fetch(`${API_URL}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw: rawText }),
  });

  if (!res.ok) {
    throw new Error(`Ingest failed: ${res.status}`);
  }

  const data = await res.json();
  return {
    id: data.id,
    raw_text: rawText,
    ingested_at: new Date().toISOString(),
    status: data.status,
    message: data.message,
    title: data.title,
    storage: data.storage,
  };
}
