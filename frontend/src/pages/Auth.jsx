import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import api from "../api";
import { useAuth } from "../context/AuthContext";

function AuthPage() {
  const [tab, setTab] = useState("login");
  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [registerData, setRegisterData] = useState({ name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const { isLoggedIn, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const nextPath = location.state?.from?.pathname || "/";

  useEffect(() => {
    if (isLoggedIn) {
      navigate("/", { replace: true });
    }
  }, [isLoggedIn, navigate]);

  const applyLogin = (data) => {
    const token = data?.token || data?.access_token;
    const name = data?.name || data?.user_name;
    login(token, name);
    navigate(nextPath, { replace: true });
  };

  const onLogin = async (event) => {
    event.preventDefault();
    setError("");
    try {
      setLoading(true);
      const { data } = await api.post("/login", loginData);
      applyLogin(data);
    } catch (e) {
      setError(e?.response?.data?.detail || "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  const onRegister = async (event) => {
    event.preventDefault();
    setError("");
    try {
      setLoading(true);
      const { data } = await api.post("/register", registerData);
      applyLogin(data);
    } catch (e) {
      setError(e?.response?.data?.detail || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex flex-1 items-center justify-center bg-surface px-gutter py-16">
        <div className="w-full max-w-[440px]">
          <div className="flex flex-col items-center mb-xl">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center mb-md">
              <span className="material-symbols-outlined text-on-primary">precision_manufacturing</span>
            </div>
            <h1 className="font-h1 text-h1 text-on-surface">AI Intelligence Hub</h1>
          </div>

          <div className="bg-white border border-outline-variant rounded-xl shadow-[0px_4px_6px_rgba(0,0,0,0.05)] overflow-hidden">
            <div className="flex border-b border-outline-variant">
              <button onClick={() => setTab("login")} className={`flex-1 py-md font-button text-button ${tab === "login" ? "text-primary border-b-2 border-primary bg-surface-container-lowest" : "text-secondary hover:bg-surface-container-low"}`}>
                Login
              </button>
              <button onClick={() => setTab("register")} className={`flex-1 py-md font-button text-button ${tab === "register" ? "text-primary border-b-2 border-primary bg-surface-container-lowest" : "text-secondary hover:bg-surface-container-low"}`}>
                Register
              </button>
            </div>

            <div className="p-xl space-y-lg">
              {tab === "login" ? (
                <form className="space-y-md" onSubmit={onLogin}>
                  <div className="space-y-xs">
                    <label className="font-label-md text-label-md text-on-surface-variant" htmlFor="email">Email Address</label>
                    <div className="relative">
                      <span className="material-symbols-outlined absolute left-md top-1/2 -translate-y-1/2 text-outline text-[20px]">mail</span>
                      <input id="email" type="email" value={loginData.email} onChange={(e) => setLoginData((p) => ({ ...p, email: e.target.value }))} className="w-full pl-[44px] pr-md py-sm bg-white border border-outline-variant rounded-lg font-body-md text-body-md focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all" placeholder="name@company.com" required />
                    </div>
                  </div>
                  <div className="space-y-xs">
                    <label className="font-label-md text-label-md text-on-surface-variant" htmlFor="password">Password</label>
                    <div className="relative">
                      <span className="material-symbols-outlined absolute left-md top-1/2 -translate-y-1/2 text-outline text-[20px]">lock</span>
                      <input id="password" type="password" value={loginData.password} onChange={(e) => setLoginData((p) => ({ ...p, password: e.target.value }))} className="w-full pl-[44px] pr-md py-sm bg-white border border-outline-variant rounded-lg font-body-md text-body-md focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all" placeholder="••••••••" required />
                    </div>
                  </div>
                  <button className="w-full bg-primary text-on-primary py-sm rounded-lg font-button text-button hover:opacity-90 active:scale-[0.98] transition-all" disabled={loading}>
                    {loading ? "Signing In..." : "Sign In"}
                  </button>
                </form>
              ) : (
                <form className="space-y-md" onSubmit={onRegister}>
                  <input type="text" value={registerData.name} onChange={(e) => setRegisterData((p) => ({ ...p, name: e.target.value }))} className="w-full px-md py-sm bg-white border border-outline-variant rounded-lg font-body-md text-body-md focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all" placeholder="Full name" required />
                  <input type="email" value={registerData.email} onChange={(e) => setRegisterData((p) => ({ ...p, email: e.target.value }))} className="w-full px-md py-sm bg-white border border-outline-variant rounded-lg font-body-md text-body-md focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all" placeholder="name@company.com" required />
                  <input type="password" value={registerData.password} onChange={(e) => setRegisterData((p) => ({ ...p, password: e.target.value }))} className="w-full px-md py-sm bg-white border border-outline-variant rounded-lg font-body-md text-body-md focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all" placeholder="••••••••" required />
                  <button className="w-full bg-primary text-on-primary py-sm rounded-lg font-button text-button hover:opacity-90 active:scale-[0.98] transition-all" disabled={loading}>
                    {loading ? "Creating Account..." : "Create Account"}
                  </button>
                </form>
              )}

              {error ? <p className="font-body-md text-body-md text-error">{error}</p> : null}
            </div>
          </div>

          <p className="mt-lg text-center font-label-md text-label-md text-on-surface-variant">
            By signing in, you agree to our <a className="text-primary hover:underline" href="/terms">Terms of Service</a> and <a className="text-primary hover:underline" href="/privacy">Privacy Policy</a>.
          </p>
        </div>
      </main>
  );
}

export default AuthPage;
