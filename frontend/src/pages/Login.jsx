import React, { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useUserAuth } from "../context/UserAuthContext";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { user, loading, setUser } = useUserAuth();
  const navigate = useNavigate();

  // 1. Check if user is already logged in
  if (loading) return <div>Loading...</div>;

  if (user) {
    return <Navigate to="/user/project" replace />;
  }

  const handleLogin = async (e) => {
    e.preventDefault();

    // 1. Create the FormData object
    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);

    // 2. Send the POST request to the backend
    try {
      const response = await fetch("http://localhost:8000/api/v1/user/login", {
        method: "POST",
        body: formData,
        credentials: "include",
      });
      // console.log("Login response status:", response.status);
      if (response.ok) {
        const data = await response.json();

        // 1. Check the JSON body, NOT the cookie
        console.log("Login response data:", data);
        if (data.user) {
          console.log("Login successful!");
          setUser(data.user); // Update the user state in AuthContext
          navigate("/project", { replace: true });
        } else {
          console.log("Login failed: No user in response body");
        }
      }
    } catch (error) {
      console.error("Login error:", error);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md w-96">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">
          Welcome Back
        </h2>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              type="email"
              required
              className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-sm shadow-sm placeholder-gray-400
                         focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              type="password"
              required
              className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-sm shadow-sm placeholder-gray-400
                         focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Sign In
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
