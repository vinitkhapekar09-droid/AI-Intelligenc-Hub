import { createContext, useContext, useEffect, useMemo, useState } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState("");
  const [userName, setUserName] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const savedToken = localStorage.getItem("token") || "";
    const savedName = localStorage.getItem("userName") || "";
    const savedLoggedIn = localStorage.getItem("isLoggedIn") === "true";

    setToken(savedToken);
    setUserName(savedName);
    setIsLoggedIn(savedLoggedIn && Boolean(savedToken));
  }, []);

  const login = (nextToken, name) => {
    setToken(nextToken);
    setUserName(name);
    setIsLoggedIn(true);

    localStorage.setItem("token", nextToken);
    localStorage.setItem("userName", name);
    localStorage.setItem("isLoggedIn", "true");
  };

  const logout = () => {
    setToken("");
    setUserName("");
    setIsLoggedIn(false);
    localStorage.clear();
  };

  const value = useMemo(() => ({ token, userName, isLoggedIn, login, logout }), [token, userName, isLoggedIn]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
