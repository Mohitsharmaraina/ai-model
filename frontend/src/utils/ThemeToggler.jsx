import React, { useState, useEffect } from "react";
import { Sun, Moon } from "lucide-react";
const ThemeToggler = () => {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    // This ensures React matches what the index.html script just did
    if (typeof window !== "undefined") {
      return document.documentElement.classList.contains("dark");
    }
    return true; // fallback
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (isDarkMode) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [isDarkMode]);
  return (
    <button
      onClick={() => setIsDarkMode(!isDarkMode)}
      className="p-2 rounded-md hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-500 transition-colors"
    >
      {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
};

export default ThemeToggler;
