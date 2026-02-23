import React, { useState, useEffect, useRef } from "react";
import MessageRenderer from "../utils/MessageRenderer";
import {
  MessageSquare,
  Plus,
  FolderPlus,
  Image as ImageIcon,
  Send,
  Sun,
  Moon,
  User,
  MoreVertical,
  Pencil,
  X,
  Check,
} from "lucide-react";

export default function AIChatInterface() {
  // --- STATE ---
  const [isDarkMode, setIsDarkMode] = useState(() => {
    // This ensures React matches what the index.html script just did
    if (typeof window !== "undefined") {
      return document.documentElement.classList.contains("dark");
    }
    return true; // fallback
  });
  const [sessions, setSessions] = useState();
  //     [
  //     { id: "1", title: "React component help", folderId: null },
  //     { id: "2", title: "Explain Quantum Physics", folderId: "f1" },
  //   ]
  const [folders, setFolders] = useState([
    { id: "f1", name: "Science Studies" },
  ]);
  const [currentSessionId, setCurrentSessionId] = useState(
    localStorage.getItem("currentSessionId") || "1",
  );
  const [messages, setMessages] = useState();
  //     [
  //     { id: 1, role: "ai", content: "Hello! How can I help you today?" },
  //   ]
  const [inputText, setInputText] = useState("");

  //   states for image upload
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  //   states for editing session title
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState("");
  const [editingSessionId, setEditingSessionId] = useState(null);
  const inputRef = useRef(null);

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

  //   ------------------ Edit session title handlers ------------------------

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  const handleSave = async (session) => {
    const trimmedValue = editValue.trim();
    // Only save if the title actually changed and isn't empty
    if (trimmedValue && trimmedValue !== session.title) {
      try {
        const response = await fetch(
          `http://127.0.0.1:8000/api/v1/user_prompts/sessions/${session.session_id}`,
          {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTgwOWI0NjJmZWViMTUzOGVkNjJhYTMiLCJpc0FkbWluIjoiVHJ1ZSIsImV4cCI6MTc3MTg2MzY5MH0.7XOJWmt_piGA0Yeox4LNmNyo6rqjWujNpvLeJWxM9So"}`,
            },
            body: JSON.stringify({ title: trimmedValue }),
          },
        );
        if (!response.ok) {
          throw new Error("Failed to update session title");
        }
        // Update the session in the state
        setSessions((prevSessions) =>
          prevSessions.map((s) =>
            s.session_id === session.session_id
              ? { ...s, title: trimmedValue }
              : s,
          ),
        );
      } catch (error) {
        console.error("Error updating session title:", error);
      }
    }
    setIsEditing(false);
    setEditValue(""); // Clear edit value after saving or if no change was made
  };

  const handleCancel = (session) => {
    setEditValue(session.title); // Reset to original
    setIsEditing(false);
  };

  const handleKeyDown = (e, session) => {
    if (e.key === "Enter") handleSave(session);
    if (e.key === "Escape") handleCancel(session);
  };

  //  ----------------- get all sessions for current user and set to state------------------------

  useEffect(() => {
    getAllSessionsForCurrentUser();
  }, [isEditing]);

  const getAllSessionsForCurrentUser = async () => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/v1/user_prompts/sessions",
        {
          headers: {
            Authorization: `Bearer ${"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTgwOWI0NjJmZWViMTUzOGVkNjJhYTMiLCJpc0FkbWluIjoiVHJ1ZSIsImV4cCI6MTc3MTg2MzY5MH0.7XOJWmt_piGA0Yeox4LNmNyo6rqjWujNpvLeJWxM9So"}`,
          },
        },
      );
      if (!response.ok) {
        throw new Error("Failed to fetch sessions");
      }

      const sessions = await response.json();
      console.log("Fetched sessions:", sessions);
      setSessions(sessions);
    } catch (error) {
      console.error("Error fetching sessions:", error);
    }
  };

  //   ----------------- get all messages for current session and set to state------------------------

  useEffect(() => {
    console.log("session_id for session:", currentSessionId);
  }, [currentSessionId, messages]);

  useEffect(() => {
    if (!currentSessionId) return;
    getMessagesForCurrentSession();
  }, [currentSessionId]);

  const getMessagesForCurrentSession = async () => {
    if (!currentSessionId) return;

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/v1/user_prompts/sessions/${currentSessionId}`,
        {
          headers: {
            Authorization: `Bearer ${"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTgwOWI0NjJmZWViMTUzOGVkNjJhYTMiLCJpc0FkbWluIjoiVHJ1ZSIsImV4cCI6MTc3MTg2MzY5MH0.7XOJWmt_piGA0Yeox4LNmNyo6rqjWujNpvLeJWxM9So"}`,
          },
        },
      );
      if (!response.ok) {
        throw new Error("Failed to fetch messages");
      }

      const messages = await response.json();
      const turns = messages.turns?.map((turn) => ({
        key: turn.turn_id,
        session_id: messages.session_id,
        turn_id: turn.turn_id,
        user_query: turn.user.content[0].text,
        model_response: turn.assistant.content[0].text,
      }));
      console.log("Fetched messages:", messages.turns);
      setMessages(turns);
    } catch (error) {
      console.error("Error fetching messages:", error);
    }
  };

  // --- HANDLERS ---
  const handleNewChat = () => {
    // Generate a new ID to simulate backend session creation
    const session_id = crypto.randomUUID();

    setCurrentSessionId(session_id);
    localStorage.setItem("currentSessionId", session_id);
    setMessages([]);
    getAllSessionsForCurrentUser(); // Refresh session list to include the new session
  };

  const handleNewFolder = () => {
    const newFolderId = `folder_${Date.now()}`;
    const folderName = prompt("Enter folder name:");
    if (folderName) {
      setFolders([...folders, { id: newFolderId, name: folderName }]);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    // Add User Message
    const userMsg = inputText.trim();
    const session_id = currentSessionId;

    // Simulate AI Response
    const formData = new FormData();
    formData.append("session_id", session_id);
    formData.append("message", userMsg);

    if (file) {
      formData.append("images", file);
    }

    const userTurn = {
      turn_id: crypto.randomUUID(),
      session_id,
      user_query: userMsg,
      model_response: "AI is typing...", // Placeholder until we get the real response
    };

    setMessages((prev) => [...prev, userTurn]);

    setInputText("");
    clearImage();
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/v1/user_prompts/chat",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTgwOWI0NjJmZWViMTUzOGVkNjJhYTMiLCJpc0FkbWluIjoiVHJ1ZSIsImV4cCI6MTc3MTg2MzY5MH0.7XOJWmt_piGA0Yeox4LNmNyo6rqjWujNpvLeJWxM9So"}`,
          },
          body: formData,
        },
      );

      if (response.ok) {
        const data = await response.json();
        setMessages((prev) =>
          prev.map((m) =>
            m.turn_id === userTurn.turn_id
              ? { ...m, model_response: data.response } // Assuming 'data' matches your turn structure
              : m,
          ),
        );
      } else {
        throw new Error("Server error");
      }
    } catch (error) {
      // If the API fails, update the placeholder with an error message
      setMessages((prev) =>
        prev.map((m) =>
          m.turn_id === userTurn.turn_id
            ? {
                ...m,
                model_response:
                  "Couldn't generate response! Try again later :(",
              }
            : m,
        ),
      );
    }
  };

  const handleImageUpload = () => {
    fileInputRef.current.click();
  };

  const onFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      const reader = new FileReader();
      setImagePreview(URL.createObjectURL(selectedFile));
    }
  };

  const clearImage = () => {
    setFile(null);
    setImagePreview(null);
    fileInputRef.current.value = null;
  };

  return (
    <div className="flex h-screen w-full bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-200 font-sans overflow-hidden transition-colors duration-200">
      {/* --- SIDEBAR --- */}
      <aside className="w-64 border-r border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-950 flex flex-col transition-colors duration-200">
        {/* Sidebar Actions */}
        <div className="p-4 space-y-2">
          <button
            onClick={handleNewChat}
            className="flex items-center w-full gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <Plus size={18} />
            <span className="font-medium text-sm">New Chat</span>
          </button>
          <button
            onClick={handleNewFolder}
            className="flex items-center w-full gap-2 px-3 py-2 bg-transparent hover:bg-gray-200 dark:hover:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg transition-colors text-sm"
          >
            <FolderPlus size={18} />
            <span>New Folder</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wider pl-2 mt-4">
            Search History
          </div>
          {sessions &&
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => {
                  setCurrentSessionId(session.session_id);
                  localStorage.setItem("currentSessionId", session.session_id);
                }}
                className={`group flex items-center w-full gap-2 px-3 py-2 rounded-lg text-sm text-left truncate transition-colors ${
                  currentSessionId === session.session_id
                    ? "bg-gray-200 dark:bg-gray-800 font-medium"
                    : "hover:bg-gray-200 dark:hover:bg-gray-800/50"
                }`}
              >
                <MessageSquare size={16} className="shrink-0" />
                {isEditing && editingSessionId === session.session_id ? (
                  <div className="flex items-center w-full gap-2">
                    <input
                      ref={inputRef}
                      type="text"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onKeyDown={(e) => handleKeyDown(e, session)}
                      onBlur={() => handleSave(session)} // Saves when the user clicks away
                      className="flex-1 bg-transparent border-b border-blue-500 outline-none text-sm px-1 max-w-35 overflow-x-auto"
                    />
                    {/* Optional: Add explicit save/cancel buttons */}
                    <Check
                      onClick={() => handleSave(session)}
                      size={16}
                      className="text-green-500 cursor-pointer hover:text-green-600"
                    />
                    <X
                      onClick={() => handleCancel(session)}
                      size={16}
                      className="text-red-500 cursor-pointer hover:text-red-600"
                    />
                  </div>
                ) : (
                  <>
                    <span className="truncate">{session.title}</span>
                    <Pencil
                      onClick={() => {
                        setIsEditing(true);
                        setEditingSessionId(session.session_id);
                      }}
                      size={14}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors cursor-pointer ml-auto invisible group-hover:visible"
                    />
                  </>
                )}
              </button>
            ))}
        </div>

        {/* User Profile & Theme Toggle */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="bg-blue-100 dark:bg-blue-900 p-2 rounded-full shrink-0">
              <User size={18} className="text-blue-600 dark:text-blue-300" />
            </div>
            <div className="truncate">
              <div className="text-sm font-medium truncate">Alex Developer</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                alex@example.com
              </div>
            </div>
          </div>
          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            className="p-2 rounded-md hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-500 transition-colors"
          >
            {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </aside>

      {/* --- MAIN BODY --- */}
      <main className="flex-1 flex flex-col h-full relative">
        {/* Header */}
        <header className="h-14 border-b border-gray-200 dark:border-gray-800 flex items-center px-4 justify-between">
          <h1 className="font-medium text-lg">
            {sessions?.find((s) => s.id === currentSessionId)?.title || "Chat"}
          </h1>
          <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md">
            <MoreVertical size={18} className="text-gray-500" />
          </button>
        </header>

        {/* Chat Messages Area */}

        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages?.map((turn) => (
            <React.Fragment key={turn.turn_id}>
              {/* 1. USER QUERY (Right Aligned) */}
              <div className="flex w-full justify-end">
                <div className="max-w-[75%] rounded-2xl p-4 bg-blue-600 text-white rounded-br-sm shadow-sm">
                  <p className="text-sm leading-relaxed">{turn.user_query}</p>
                </div>
              </div>

              {/* 2. MODEL RESPONSE (Left Aligned) */}
              <div className="flex w-full justify-start">
                <div className="max-w-[75%] rounded-2xl p-4 bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-bl-sm shadow-sm overflow-x-auto">
                  {/* If your model returns markdown, you'd use a markdown library here */}
                  <MessageRenderer content={turn.model_response} />
                </div>
              </div>
            </React.Fragment>
          ))}
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
          {imagePreview && (
            <div className="max-w-4xl mx-auto mb-2 relative inline-block">
              <img
                src={imagePreview}
                alt="preview"
                className="h-20 w-20 object-cover rounded-lg border border-gray-300 dark:border-gray-700"
              />
              <button
                onClick={clearImage}
                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 shadow-lg hover:bg-red-600"
              >
                <X size={12} /> {/* Import X from lucide-react */}
              </button>
            </div>
          )}

          <form
            onSubmit={handleSendMessage}
            className="max-w-4xl mx-auto relative flex items-center gap-2 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-300 dark:border-gray-700 p-2 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent transition-all"
          >
            {/* hidden file input */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={onFileChange}
              accept="image/*"
              className="hidden"
            />
            <button
              type="button"
              onClick={handleImageUpload}
              className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title="Upload Image"
            >
              <ImageIcon size={20} />
            </button>

            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Message the AI model..."
              className="flex-1 bg-transparent border-none outline-none text-sm px-2 text-gray-800 dark:text-gray-200 placeholder-gray-400"
            />

            <button
              type="submit"
              disabled={!inputText.trim()}
              className="p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 dark:disabled:bg-blue-800 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center justify-center"
            >
              <Send size={18} />
            </button>
          </form>
          <p className="text-center text-xs text-gray-400 mt-2">
            AI models can make mistakes. Verify important information.
          </p>
        </div>
      </main>
    </div>
  );
}
