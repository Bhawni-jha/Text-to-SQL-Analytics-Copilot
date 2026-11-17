import { useState } from "react";

export default function AuthPanel({ user, onAuth, onLogout }) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await onAuth(mode, email, password);
      setOpen(false);
      setPassword("");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (user) {
    return (
      <div className="account-actions">
        <span className="user-chip">{user.email}</span>
        <button type="button" className="btn small dark-btn" onClick={onLogout}>Sign out</button>
      </div>
    );
  }

  return (
    <div className="auth-wrap">
      <button type="button" className="btn small dark-btn" onClick={() => setOpen((value) => !value)}>
        Sign in
      </button>
      {open && (
        <form className="auth-popover" onSubmit={submit}>
          <div className="auth-tabs">
            <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>Sign in</button>
            <button type="button" className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>Create account</button>
          </div>
          <input type="email" placeholder="Email address" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <input type="password" placeholder="Password (8+ characters)" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required />
          {error && <p className="auth-error">{error}</p>}
          <button type="submit" className="btn primary" disabled={busy}>{busy ? "Working…" : mode === "login" ? "Continue" : "Create account"}</button>
        </form>
      )}
    </div>
  );
}
