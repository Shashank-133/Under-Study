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

/**
 * Ingestion stub until Person 2 adds POST /ingest.
 * Simulates pipeline delay and returns a local record for the demo UI.
 */
export async function ingestIncident(rawText) {
  await new Promise((resolve) => setTimeout(resolve, 1500));

  return {
    id: `local-${Date.now()}`,
    raw_text: rawText,
    ingested_at: new Date().toISOString(),
    status: "stub",
    message:
      "Incident recorded locally for demo. When the backend ingest endpoint is live, this will write to Neo4j.",
  };
}
