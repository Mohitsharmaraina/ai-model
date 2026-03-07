import { Navigate, Outlet } from "react-router-dom";
import { useUserAuth } from "../../context/UserAuthContext";

const ProtectedRoute = () => {
  const { user, loading } = useUserAuth();

  if (loading) return <div>Loading...</div>;

  // if (!user) {
  //   return <Navigate to="/login" replace />;
  // }

  return <Outlet />;
};

export default ProtectedRoute;
