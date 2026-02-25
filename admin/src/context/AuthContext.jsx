import react, { createContext, useState, useEffect, useContext } from "react";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fineTunedModels, setFineTunedModels] = useState([]);

  const checkSession = async () => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/v1/user/validate-token",
        {
          credentials: "include",
        },
      );

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
      } else {
        setUser(null);
      }
    } catch (error) {
      setUser(null);
      console.error("Error validating token:", error);
    } finally {
      setLoading(false);
    }
  };

  const getFineTunedModels = async () => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/v1/admin/trained-models",
        {
          credentials: "include",
        },
      );
      if (response.ok) {
        const data = await response.json();
        const models = [
          ...new Set(data.map((model) => model.fine_tuned_model)),
        ];

        setFineTunedModels(models);
      }
    } catch (error) {
      console.error("Error fetching fine-tuned models:", error);
    }
  };

  useEffect(() => {
    checkSession();
    getFineTunedModels();
  }, []);

  const logout = async () => {
    await fetch("http://localhost:8000/api/v1/user/logout", {
      method: "POST",
      credentials: "include",
    });
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, setUser, loading, logout, fineTunedModels }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
