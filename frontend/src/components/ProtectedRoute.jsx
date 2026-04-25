import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function ProtectedRoute({ children }) {
  const { isLoggedIn, isLoading } = useAuth();
  const location = useLocation();
  
  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center text-on-surface">Loading...</div>;
  }
  
  if (!isLoggedIn) return <Navigate to="/auth" replace state={{ from: location }} />;
  return children;
}

export default ProtectedRoute;
