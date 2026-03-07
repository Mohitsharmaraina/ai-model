// import React, { createContext, useContext, useEffect, useState } from "react";

// const AuthContext = createContext();

// export const UserAuthProvider = ({ children }) => {
//   const [user, setUser] = useState(null);
//   const [loading, setLoading] = useState(true);
//   const [activeModel, setActiveModel] = useState("gpt-4o-2024-08-06");

//   // ------------------get active model from databae-----------------
//   const getActiveModel = async () => {
//     try {
//       const response = await fetch(
//         "http://localhost:8000/api/v1/user/active-model",
//         {
//           credentials: "include",
//         },
//       );

//       if (response.ok) {
//         const data = await response.json();
//         setActiveModel(data.active_model);
//       }
//     } catch (error) {
//       console.error("Error fetching active model:", error);
//     }
//   };

//   const checkSession = async () => {
//     try {
//       const response = await fetch(
//         "http://localhost:8000/api/v1/user/validate-token",
//         {
//           credentials: "include",
//         },
//       );

//       if (response.ok) {
//         const data = await response.json();
//         setUser(data.user);
//       } else {
//         setUser(null);
//       }
//     } catch (error) {
//       setUser(null);
//       console.error("Error validating token:", error);
//     } finally {
//       setLoading(false);
//     }
//   };

//   useEffect(() => {
//     getActiveModel();
//     checkSession();
//   }, []);

//   const logout = async () => {
//     await fetch("http://localhost:8000/api/v1/user/logout", {
//       method: "POST",
//       credentials: "include",
//     });
//     localStorage.removeItem("currentSessionId");
//     setUser(null);
//   };

//   return (
//     <AuthContext.Provider
//       value={{ user, setUser, loading, logout, activeModel }}
//     >
//       {children}
//     </AuthContext.Provider>
//   );
// };

// export const useUserAuth = () => {
//   return useContext(AuthContext);
// };

import React, { createContext, useContext, useEffect, useState } from "react";
import { useAuth, useUser } from "@clerk/react";

const AppContext = createContext();

export const UserAuthProvider = ({ children }) => {
  const { user, isLoaded } = useUser();
  const { getToken, signOut } = useAuth();

  const [activeModel, setActiveModel] = useState("gpt-4o-2024-08-06");
  const [loading, setLoading] = useState(true);

  // Fetch model from backend
  const getActiveModel = async () => {
    try {
      const token = await getToken();

      const response = await fetch(
        "http://localhost:8000/api/v1/user_prompts/active-model",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (response.ok) {
        const data = await response.json();
        setActiveModel(data.active_model);
      }
    } catch (error) {
      console.error("Error fetching active model:", error);
    }
  };

  useEffect(() => {
    if (isLoaded && user) {
      getActiveModel();
      setLoading(false);
    }
  }, [isLoaded, user]);

  const logout = async () => {
    await signOut();
  };

  return (
    <AppContext.Provider
      value={{
        user,
        loading,
        logout,
        activeModel,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useUserAuth = () => {
  return useContext(AppContext);
};
