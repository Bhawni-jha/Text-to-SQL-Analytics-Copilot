// Small wrapper around fetch. All calls go to /api (proxied to FastAPI by vite.config.js).
let authToken = localStorage.getItem("sql-copilot-token") || "";

export function setAuthToken(token) {
  authToken = token || "";
  if (authToken) localStorage.setItem("sql-copilot-token", authToken);
  else localStorage.removeItem("sql-copilot-token");
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (authToken) headers.Authorization = `Bearer ${authToken}`;
  const res = await fetch(`/api${path}`, {
    headers,
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

export const askQuestion = (question, tables = []) =>
  request("/ask", { method: "POST", body: JSON.stringify({ question, tables }) });

export const runSql = (sql) =>
  request("/run", { method: "POST", body: JSON.stringify({ sql }) });

export const getHistory = () => request("/history");
export const deleteHistory = (id) => request(`/history/${id}`, { method: "DELETE" });
export const clearHistory = () => request("/history", { method: "DELETE" });
export const getSchema = () => request("/schema");
export const getHealth = () => request("/health");
export const register = (email, password) =>
  request("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) });
export const login = (email, password) =>
  request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
export const getCurrentUser = () => request("/auth/me");
export const getDashboards = () => request("/dashboards").then((data) => data.items || []);
export const saveDashboard = (dashboard) =>
  request("/dashboards", { method: "POST", body: JSON.stringify(dashboard) });
export const deleteDashboard = (id) =>
  request(`/dashboards/${id}`, { method: "DELETE" });
export const testConnection = (url) =>
  request("/connections/test", { method: "POST", body: JSON.stringify({ url }) });
