import { createContext, useContext, useEffect, useMemo, useState } from "react";
import api from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState("");
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscriptionStatusLoaded, setSubscriptionStatusLoaded] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem("token") || "";
    const savedName = localStorage.getItem("userName") || "";
    const savedEmail = localStorage.getItem("userEmail") || "";
    const savedLoggedIn = localStorage.getItem("isLoggedIn") === "true";

    setToken(savedToken);
    setUserName(savedName);
    setUserEmail(savedEmail);
    setIsLoggedIn(savedLoggedIn && Boolean(savedToken));
    setIsLoading(false);
  }, []);

  useEffect(() => {
    const refreshProfile = async () => {
      if (!token) {
        setIsSubscribed(false);
        setSubscriptionStatusLoaded(true);
        return;
      }

      try {
        const { data } = await api.get("/me");
        setUserName(data?.name || "");
        setUserEmail(data?.email || "");
        setIsSubscribed(Boolean(data?.is_subscribed));
        if (data?.name) {
          localStorage.setItem("userName", data.name);
        }
        if (data?.email) {
          localStorage.setItem("userEmail", data.email);
        }
      } catch {
        setIsSubscribed(false);
      } finally {
        setSubscriptionStatusLoaded(true);
      }
    };

    setSubscriptionStatusLoaded(false);
    refreshProfile();
  }, [token]);

  const login = (nextToken, name, email = "") => {
    setToken(nextToken);
    setUserName(name);
    setUserEmail(email);
    setIsLoggedIn(true);
    setIsSubscribed(false);

    localStorage.setItem("token", nextToken);
    localStorage.setItem("userName", name);
    localStorage.setItem("userEmail", email);
    localStorage.setItem("isLoggedIn", "true");
  };

  const logout = () => {
    setToken("");
    setUserName("");
    setUserEmail("");
    setIsSubscribed(false);
    setSubscriptionStatusLoaded(false);
    setIsLoggedIn(false);
    localStorage.clear();
  };

  const value = useMemo(
    () => ({ token, userName, userEmail, isSubscribed, subscriptionStatusLoaded, isLoggedIn, isLoading, login, logout, setIsSubscribed }),
    [token, userName, userEmail, isSubscribed, subscriptionStatusLoaded, isLoggedIn, isLoading]
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
