import {
  BrowserRouter as Router,
  Route,
  Routes,
  Outlet,
} from "react-router-dom";
// import ProtectedRoute from "./users/ProtectedRoute.jsx";
import AIChatInterface from "./users/ChatInterface.jsx";
import AdminPanel from "./admin/Dashboard.jsx";
import FineTuningView from "./admin/FineTuning.jsx";
import LoginPage from "./Login.jsx";
import SignInPage from "./SignIn.jsx";
import AdminLayout from "../components/AdminLayout.jsx";
import UnauthorizedPage from "./Unauthorized.jsx";
import { useUser, useOrganization } from "@clerk/react";

function UserProtectedRoute() {
  const { isSignedIn, isLoaded } = useUser();
  const { membership } = useOrganization();
  if (!isLoaded) return null;
  if (!isSignedIn) return <UnauthorizedPage />;

  const role = membership?.role;

  if (role === "org:admin" || role === "org:member") {
    return <Outlet context={{ role }} />;
  }

  return <UnauthorizedPage />;
}

function AppRoutes() {
  return (
    <Router>
      <Routes>
        {/*user Protected Routes */}
        <Route element={<UserProtectedRoute />}>
          <Route path="/user/project" element={<AIChatInterface />} />
          {/* Add more private routes here as your app grows */}
        </Route>

        {/* Admin Protected Routes */}
        <Route path="/admin" element={<AdminLayout />}>
          {/* <Route path="/admin" element={<AdminPanel />} /> */}
          <Route path="/admin/finetuning" element={<FineTuningView />} />
        </Route>

        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />

        {/* Default Route */}
        <Route path="/" element={<LoginPage />} />
        <Route path="/sign-in/*" element={<SignInPage />} />
      </Routes>
    </Router>
  );
}

export default AppRoutes;
