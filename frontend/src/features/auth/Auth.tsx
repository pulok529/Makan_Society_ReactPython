import React, { FormEvent, useState } from "react";
import { UserProfile, TokenPair } from "../../shared/types/models";
import { apiBaseUrl } from "../../shared/api/client";
import { fetchProfile } from "../../shared/utils/formatters";

const accessTokenKey = "society-modern-access-token";
const refreshTokenKey = "society-modern-refresh-token";

type AuthProps = {
  onLoginSuccess: (profile: UserProfile) => void;
};

export function Auth({ onLoginSuccess }: AuthProps) {
  const [formMode, setFormMode] = useState<"login" | "bootstrap">("login");
  const [loginName, setLoginName] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setMessage("Signing in...");
    try {
      const response = await fetch(`${apiBaseUrl}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ login_name: loginName, password }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail ?? "Login failed");
      }
      const payload = (await response.json()) as TokenPair;
      localStorage.setItem(accessTokenKey, payload.access_token);
      localStorage.setItem(refreshTokenKey, payload.refresh_token);
      const user = await fetchProfile(payload.access_token);
      setMessage("Signed in.");
      onLoginSuccess(user);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Login failed");
      setIsSubmitting(false);
    }
  }

  async function handleBootstrap(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setMessage("Creating first admin...");
    try {
      const response = await fetch(`${apiBaseUrl}/api/auth/bootstrap-admin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, login_name: loginName, email: email || null, password }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail ?? "Unable to create admin");
      }
      setFormMode("login");
      setMessage("Admin created. Log in with the same credentials.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to create admin");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-bg d-flex min-vh-100 justify-content-center align-items-center">
      <div className="row g-0 justify-content-center w-100 m-xxl-5 px-xxl-4 m-3">
        <div className="col-xl-4 col-lg-5 col-md-6">
          <div className="card overflow-hidden text-center h-100 p-xxl-4 p-3 mb-0">
            <a href="#" onClick={(event) => event.preventDefault()} className="auth-brand mb-4">
              <img src="/makan-logo-2.png" alt="Makan Society" className="logo-dark app-brand-logo" />
              <img src="/makan-logo-2.png" alt="Makan Society" className="logo-light app-brand-logo" />
            </a>
            <h4 className="fw-semibold mb-2 fs-18">
              {formMode === "login" ? "Log in to your account" : "Create first admin"}
            </h4>
            <p className="text-muted mb-4">
              {formMode === "login"
                ? "Enter your login name and password to access society admin panel."
                : "Set up the first administrator account."}
            </p>

            {message && <div className="alert alert-info py-2">{message}</div>}

            <div className="d-flex gap-2 mb-3">
              <button
                className={formMode === "login" ? "btn btn-primary w-100" : "btn btn-light w-100"}
                onClick={() => setFormMode("login")}
                type="button"
              >
                Login
              </button>
              <button
                className={formMode === "bootstrap" ? "btn btn-primary w-100" : "btn btn-light w-100"}
                onClick={() => setFormMode("bootstrap")}
                type="button"
              >
                First Admin
              </button>
            </div>

            {formMode === "bootstrap" ? (
              <form className="text-start mb-3" onSubmit={handleBootstrap}>
                <div className="mb-3">
                  <label className="form-label">Username</label>
                  <input
                    className="form-control"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    required
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Login Name</label>
                  <input
                    className="form-control"
                    value={loginName}
                    onChange={(event) => setLoginName(event.target.value)}
                    required
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Email</label>
                  <input
                    className="form-control"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Password</label>
                  <input
                    className="form-control"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                  />
                </div>
                <div className="d-grid">
                  <button className="btn btn-primary fw-semibold" disabled={isSubmitting} type="submit">
                    {isSubmitting ? "Creating..." : "Create Admin"}
                  </button>
                </div>
              </form>
            ) : (
              <form className="text-start mb-3" onSubmit={handleLogin}>
                <div className="mb-3">
                  <label className="form-label">Login Name</label>
                  <input
                    className="form-control"
                    value={loginName}
                    onChange={(event) => setLoginName(event.target.value)}
                    required
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Password</label>
                  <input
                    className="form-control"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                  />
                </div>
                <div className="d-flex justify-content-between mb-3">
                  <div className="form-check">
                    <input type="checkbox" className="form-check-input" id="checkbox-signin" defaultChecked />
                    <label className="form-check-label" htmlFor="checkbox-signin">
                      Remember me
                    </label>
                  </div>
                  <span className="text-muted border-bottom border-dashed">Society Login</span>
                </div>
                <div className="d-grid">
                  <button className="btn btn-primary fw-semibold" disabled={isSubmitting} type="submit">
                    {isSubmitting ? "Signing in..." : "Login"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
