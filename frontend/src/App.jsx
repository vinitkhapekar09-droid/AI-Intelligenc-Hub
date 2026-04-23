import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import AuthPage from "./pages/Auth";
import ChatPage from "./pages/Chat";
import DigestPage from "./pages/Digest";
import LandingPage from "./pages/Landing";

function App() {
  const location = useLocation();
  const hideNavbar = location.pathname === "/auth";

  return (
    <div className="min-h-screen bg-background text-on-surface">
      {!hideNavbar ? <Navbar /> : null}
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <ChatPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/digest"
          element={
            <ProtectedRoute>
              <DigestPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

export default App;
