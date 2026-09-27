import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Mail, Lock, User, Eye, EyeOff, ArrowRight } from "lucide-react";
import { useAuth } from "../context/AuthContext";

function Card({ children, className = "" }) {
  return <div className={`card ${className}`}>{children}</div>;
}

function AuthForm({ mode }) {
  const { login, register, error: authError } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    let result;
    if (mode === "login") {
      result = await login(email, password);
    } else {
      result = await register(name, email, password);
    }

    setLoading(false);
    if (result.success) {
      navigate("/");
    } else {
      setError(result.error || authError || "Something went wrong");
    }
  };

  return (
    <div className="login-page">
      <div className="login-brand">
        <div className="brand-mark">B</div>
        <div>
          <b>BISense</b>
          <span>Standards Intelligence</span>
        </div>
      </div>

      <Card className="login-card">
        <div className="eyebrow">{mode === "login" ? "WELCOME BACK" : "CREATE ACCOUNT"}</div>
        <h1>{mode === "login" ? "Enter your workspace" : "Start your BISense journey"}</h1>
        <p>{mode === "login" ? "Sign in to continue exploring Indian Standards." : "Join to search standards, track compliance, and get AI-powered insights."}</p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          {mode === "register" && (
            <div className="input-group">
              <User className="input-icon" />
              <input
                type="text"
                placeholder="Full name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoComplete="name"
              />
            </div>
          )}

          <div className="input-group">
            <Mail className="input-icon" />
            <input
              type="email"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="input-group">
            <Lock className="input-icon" />
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete={mode === "login" ? "current-password" : "new-password"}
            />
            <button
              type="button"
              className="eye-btn"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <button
            className="primary full"
            type="submit"
            disabled={loading}
          >
            {loading ? "..." : mode === "login" ? "Continue" : "Create account"}
            <ArrowRight size={16} />
          </button>
        </form>

        <p className="auth-switch">
          {mode === "login" ? "Don't have an account?" : "Already have an account?"}{" "}
          <Link to={mode === "login" ? "/register" : "/login"} onClick={() => setError("")}>
            {mode === "login" ? "Sign up" : "Sign in"}
          </Link>
        </p>

        <small className="login-note">
          Demo mode: any credentials work when backend is not connected.
        </small>
      </Card>
    </div>
  );
}

export function Login() {
  return <AuthForm mode="login" />;
}

export function Register() {
  return <AuthForm mode="register" />;
}