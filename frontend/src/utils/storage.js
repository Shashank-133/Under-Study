const PENDING_QUERY_KEY = "understudy_pending_query";
const INGESTED_KEY = "understudy_ingested_incidents";

export function getPendingQuery() {
  try {
    return sessionStorage.getItem(PENDING_QUERY_KEY) || "";
  } catch {
    return "";
  }
}

export function setPendingQuery(text) {
  try {
    if (text) {
      sessionStorage.setItem(PENDING_QUERY_KEY, text);
    } else {
      sessionStorage.removeItem(PENDING_QUERY_KEY);
    }
  } catch {
    // ignore storage errors
  }
}

export function getIngestedIncidents() {
  try {
    const raw = localStorage.getItem(INGESTED_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function addIngestedIncident(incident) {
  const existing = getIngestedIncidents();
  const updated = [incident, ...existing].slice(0, 20);
  localStorage.setItem(INGESTED_KEY, JSON.stringify(updated));
  return updated;
}
