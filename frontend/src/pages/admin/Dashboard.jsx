import React, { useState, useEffect } from "react";
import FineTuningView from "./FineTuning.jsx";
import ThemeToggler from "../../utils/ThemeToggler.jsx";
import { User } from "lucide-react";
import { useAdminAuth } from "../../context/AdminAuthContext.jsx";

const AdminPanel = () => {
  const [activeTab, setActiveTab] = useState("finetuning");
  const { user } = useAdminAuth();

  return (
    <div
      className={`min-h-screen flex w-full font-sans transition-colors duration-300  dark:bg-gray-900 bg-gray-50`}
    >
      {/* Sidebar */}
      <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col justify-between">
        <div>
          <div className="p-6 flex items-center justify-between">
            <h1 className="text-[22px] font-bold text-gray-800 dark:text-white tracking-tight">
              AI Management
            </h1>
            <ThemeToggler />
          </div>
          <nav className="mt-2 space-y-1 px-3">
            <button
              onClick={() => setActiveTab("finetuning")}
              className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === "finetuning"
                  ? "bg-blue-50 text-blue-700 dark:bg-blue-900/50 dark:text-blue-200"
                  : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
              }`}
            >
              Model Training
            </button>
            <button
              onClick={() => setActiveTab("users")}
              className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === "users"
                  ? "bg-blue-50 text-blue-700 dark:bg-blue-900/50 dark:text-blue-200"
                  : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
              }`}
            >
              View Users List
            </button>
          </nav>
        </div>
        {/* User Profile & Theme Toggle */}
        <div className="p-4 border-t border-gray-400 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="bg-blue-100 dark:bg-blue-900 p-2 rounded-full shrink-0">
              <User size={18} className="text-blue-600 dark:text-blue-300" />
            </div>
            <div className="truncate">
              <div className="text-sm font-medium truncate dark:text-gray-200 text-gray-900">
                {user?.full_name || "User"}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                {user?.email || "user@example.com"}
              </div>
            </div>
          </div>
          <ThemeToggler />
        </div>
      </aside>

      {/* Main Body */}
      <main className="flex-1 overflow-y-auto">
        <div className="py-8 px-8 sm:px-10 max-w-5xl mx-auto">
          {activeTab === "finetuning" ? <FineTuningView /> : <UsersListView />}
        </div>
      </main>
    </div>
  );
};

const UsersListView = () => (
  <div className="text-gray-900 dark:text-white text-xl">
    User management list content goes here.
  </div>
);

export default AdminPanel;
