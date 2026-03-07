// import react, { createContext, useState, useEffect, useContext } from "react";

// const AuthContext = createContext();

// export const AdminAuthProvider = ({ children }) => {
//   const [user, setUser] = useState(null);
//   const [loading, setLoading] = useState(true);
//   const [fineTunedModels, setFineTunedModels] = useState([]);

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

//   const getFineTunedModels = async () => {
//     try {
//       const response = await fetch(
//         "http://localhost:8000/api/v1/admin/trained-models",
//         {
//           credentials: "include",
//         },
//       );
//       if (response.ok) {
//         const data = await response.json();
//         const models = [
//           ...new Set(
//             data.map((model) => ({
//               datasetId: model._id,
//               status: model.is_active,
//               fineTunedModel: model.fine_tuned_model,
//             })),
//           ),
//         ];

//         setFineTunedModels(models);
//       }
//     } catch (error) {
//       console.error("Error fetching fine-tuned models:", error);
//     }
//   };

//   useEffect(() => {
//     checkSession();
//     getFineTunedModels();
//   }, []);

//   const logout = async () => {
//     await fetch("http://localhost:8000/api/v1/user/logout", {
//       method: "POST",
//       credentials: "include",
//     });
//     setUser(null);
//   };

//   return (
//     <AuthContext.Provider
//       value={{
//         user,
//         setUser,
//         loading,
//         logout,
//         fineTunedModels,
//         setFineTunedModels,
//       }}
//     >
//       {children}
//     </AuthContext.Provider>
//   );
// };

// export const useAdAuth = () => useContext(AuthContext);

// import React, { createContext, useContext, useEffect, useState } from "react";
// import { useAuth, useUser } from "@clerk/react";

// const AppContext = createContext();

import react, { createContext, useState, useEffect, useContext } from "react";
import { useAuth, useUser } from "@clerk/react";

const AuthContext = createContext();
export const AdminAuthProvider = ({ children }) => {
  const { user, isLoaded } = useUser();
  const { getToken, signOut } = useAuth();
  const [loading, setLoading] = useState(true);

  const [fineTunedModels, setFineTunedModels] = useState([]);

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
          ...new Set(
            data.map((model) => ({
              datasetId: model._id,
              status: model.is_active,
              fineTunedModel: model.fine_tuned_model,
            })),
          ),
        ];

        setFineTunedModels(models);
      }
    } catch (error) {
      console.error("Error fetching fine-tuned models:", error);
    }
  };

  useEffect(() => {
    if (isLoaded && user) {
      getFineTunedModels();
      setLoading(false);
    }
  }, [isLoaded, user]);

  const logout = async () => {
    await signOut();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        logout,
        fineTunedModels,
        setFineTunedModels,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAdminAuth = () => {
  return useContext(AuthContext);
};
