import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./context/AuthContext";
import AuthPage from "./pages/Auth";
import ChatPage from "./pages/Chat";
import DigestPage from "./pages/Digest";
import LandingPage from "./pages/Landing";
import StaticPage from "./pages/StaticPage";

function HomeRoute() {
  const { isLoggedIn, isLoading } = useAuth();

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center text-on-surface">Loading...</div>;
  }

  return isLoggedIn ? <DigestPage /> : <LandingPage />;
}

function App() {
  const location = useLocation();
  const isChatRoute = location.pathname === "/chat";

  return (
    <div className={`${isChatRoute ? "h-screen overflow-hidden" : "min-h-screen"} bg-background text-on-surface flex flex-col`}>
      <Navbar />
      <div className={`flex-1 min-h-0 ${isChatRoute ? "overflow-hidden" : ""}`}>
        <Routes>
          <Route path="/" element={<HomeRoute />} />
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
          <Route
            path="/privacy"
            element={
              <StaticPage
                title="Privacy Policy"
                description="This lightweight policy explains how AI Intelligence Hub handles account, subscription, and conversation data inside this demo product."
                sections={[
                  {
                    heading: "Account Data",
                    body: "We store the basic registration details you provide so you can sign in, keep access to protected pages, and personalize the workspace.",
                  },
                  {
                    heading: "Chat History",
                    body: "Chat conversations may be stored so your workspace can reload previous threads and provide better continuity across sessions.",
                  },
                  {
                    heading: "Digest Email",
                    body: "If you subscribe, your email address is used only to deliver the digest and related service notices.",
                  },
                ]}
              />
            }
          />
          <Route
            path="/terms"
            element={
              <StaticPage
                title="Terms of Service"
                description="These terms summarize the expected use of this application and clarify that the product is informational software, not professional advice."
                sections={[
                  {
                    heading: "Acceptable Use",
                    body: "Use the application for lawful research, reading, and productivity workflows. Do not attempt to abuse the service or interfere with other users.",
                  },
                  {
                    heading: "Content Limits",
                    body: "News and research summaries are provided for convenience and may contain source limitations, delays, or model-generated mistakes.",
                  },
                  {
                    heading: "Availability",
                    body: "The product may change over time, and features can be updated, restricted, or removed as the application evolves.",
                  },
                ]}
              />
            }
          />
          <Route
            path="/help"
            element={
              <StaticPage
                title="Help Center"
                description="A few quick pointers for getting the most out of AI Intelligence Hub."
                sections={[
                  {
                    heading: "Digest Access",
                    body: "The landing page shows a public preview. Sign in to access the full digest experience and the chat workspace.",
                  },
                  {
                    heading: "Chat Threads",
                    body: "Use New chat to start a fresh saved conversation. Clear history permanently deletes your saved messages.",
                  },
                  {
                    heading: "Support",
                    body: "If a page fails to load or a request times out, refresh the page and confirm the backend service is running and reachable from the frontend.",
                  },
                ]}
              />
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
      {!isChatRoute ? <Footer /> : null}
    </div>
  );
}

export default App;
