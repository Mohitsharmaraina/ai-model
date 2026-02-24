import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./pages/ProtectedRoute";
import AIChatInterface from "./pages/ChatInterface";
import LoginPage from "./pages/Login";
function App() {
  return (
    <Router>
      <Routes>
        {/* Protected Routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="/project" element={<AIChatInterface />} />
          {/* Add more private routes here as your app grows */}
        </Route>

        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />

        {/* Default Route */}
        <Route path="/" element={<LoginPage />} />
      </Routes>
    </Router>
  );
}

export default App;
