import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function navClass({ isActive }) {
  return `font-['Inter'] text-sm font-medium tracking-tight transition-colors ${
    isActive
      ? "text-blue-600 border-b-2 border-blue-600 pb-1"
      : "text-slate-500 hover:text-blue-600"
  }`;
}

function Navbar() {
  const { isLoggedIn, userName, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const primaryLinks = isLoggedIn
    ? [
        { to: "/", label: "Home" },
        { to: "/chat", label: "Research" },
      ]
    : [
        { to: "/", label: "Home" },
        { to: "/chat", label: "Chat" },
      ];

  const onLogout = () => {
    setMobileOpen(false);
    logout();
    navigate("/", { replace: true });
  };

  const closeMobileMenu = () => setMobileOpen(false);

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <nav className="w-full max-w-7xl mx-auto px-6 py-3">
        <div className="flex h-10 items-center justify-between gap-4">
          <Link to="/" className="text-xl font-bold text-slate-900" onClick={closeMobileMenu}>AI Intelligence Hub</Link>

          <div className="hidden md:flex items-center space-x-8">
            {primaryLinks.map((link) => (
              <NavLink key={link.to} to={link.to} className={navClass}>{link.label}</NavLink>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-3">
            {isLoggedIn ? <span className="text-sm text-slate-600">{userName}</span> : null}
            {isLoggedIn ? (
              <button onClick={onLogout} className="bg-primary text-on-primary px-4 py-2 rounded font-button text-button hover:opacity-90 transition-all">Logout</button>
            ) : (
              <button onClick={() => navigate("/auth")} className="bg-primary text-on-primary px-4 py-2 rounded font-button text-button hover:opacity-90 transition-all">Login</button>
            )}
          </div>

          <button
            aria-expanded={mobileOpen}
            aria-label="Toggle navigation menu"
            className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 text-slate-700 md:hidden"
            onClick={() => setMobileOpen((open) => !open)}
            type="button"
          >
            <span className="material-symbols-outlined text-[20px]">
              {mobileOpen ? "close" : "menu"}
            </span>
          </button>
        </div>

        {mobileOpen ? (
          <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-4 md:hidden">
            <div className="flex flex-col gap-3">
              {primaryLinks.map((link) => (
                <NavLink key={link.to} to={link.to} className={navClass} onClick={closeMobileMenu}>{link.label}</NavLink>
              ))}
            </div>
            <div className="mt-4 flex items-center justify-between gap-3 border-t border-slate-200 pt-4">
              {isLoggedIn ? <span className="text-sm text-slate-600">{userName}</span> : <span className="text-sm text-slate-500">Sign in for full access</span>}
              {isLoggedIn ? (
                <button onClick={onLogout} className="bg-primary text-on-primary px-4 py-2 rounded font-button text-button hover:opacity-90 transition-all">Logout</button>
              ) : (
                <button onClick={() => { closeMobileMenu(); navigate("/auth"); }} className="bg-primary text-on-primary px-4 py-2 rounded font-button text-button hover:opacity-90 transition-all">Login</button>
              )}
            </div>
          </div>
        ) : null}
      </nav>
    </header>
  );
}

export default Navbar;
