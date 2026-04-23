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

  const onLogout = () => {
    logout();
    navigate("/auth");
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <nav className="flex justify-between items-center w-full px-6 h-16 max-w-7xl mx-auto">
        <Link to="/" className="text-xl font-bold text-slate-900">AI Intelligence Hub</Link>
        <div className="hidden md:flex items-center space-x-8">
          <NavLink to="/" className={navClass}>Home</NavLink>
          <NavLink to="/digest" className={navClass}>Digest</NavLink>
          <NavLink to="/chat" className={navClass}>Chat</NavLink>
        </div>
        <div className="flex items-center gap-3">
          {isLoggedIn ? <span className="text-sm text-slate-600">{userName}</span> : null}
          {isLoggedIn ? (
            <button onClick={onLogout} className="bg-primary text-on-primary px-4 py-2 rounded font-button text-button hover:opacity-90 transition-all">Logout</button>
          ) : (
            <button onClick={() => navigate("/auth")} className="bg-primary text-on-primary px-4 py-2 rounded font-button text-button hover:opacity-90 transition-all">Login</button>
          )}
        </div>
      </nav>
    </header>
  );
}

export default Navbar;
