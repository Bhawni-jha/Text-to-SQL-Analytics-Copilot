// Small wrapper around fetch. All calls go to /api (proxied to FastAPI by vite.config.js).
async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  let data = null;
  try {
    data = await res.json();
  } catch {
    // no JSON body
  }

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    if (data && typeof data.detail === "string") {
      message = data.detail;
    } else if (data && Array.isArray(data.detail)) {
      message = data.detail.map((d) => d.msg).join("; ");
    }
    throw new Error(message);
  }
  return data;
}

export const askQuestion = (question) =>
  request("/ask", { method: "POST", body: JSON.stringify({ question }) });

export const runSql = (sql) =>
  request("/run", { method: "POST", body: JSON.stringify({ sql }) });

export const getHistory = () => request("/history");
export const getSchema = () => request("/schema");
export const getHealth = () => request("/health");
