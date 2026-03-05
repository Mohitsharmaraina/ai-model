// import React, { useState, useEffect, useRef } from "react";
// import { useAuth } from "../context/AuthContext";

// const TERMINAL_STATUSES = ["succeeded", "failed", "cancelled"];
// const RUNNING_STATUSES = ["validating_files", "queued", "running"];

// const FineTuningView = () => {
//   const { fineTunedModels } = useAuth();
//   const [datasetId, setDatasetId] = useState(null);

//   const [selectedModel, setSelectedModel] = useState("gpt-4o-mini-2024-07-18");
//   const [file, setFile] = useState(null);

//   const [uploadState, setUploadState] = useState("idle"); // idle, processing, ready

//   const [jobStatus, setJobStatus] = useState("idle"); // idle | validating_files | queued | running | succeeded | failed | cancelled | paused (if you ever add)
//   const [jobModel, setJobModel] = useState(null);

//   const [logs, setLogs] = useState([
//     "> System initialized. Awaiting Excel upload...",
//   ]);

//   const pollIntervalRef = useRef(null);
//   const terminalEndRef = useRef(null);

//   useEffect(() => {
//     console.log("datasetId changed:", datasetId);
//   }, [datasetId]);

//   // Auto-scroll terminal
//   useEffect(() => {
//     terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
//   }, [logs]);

//   const addLog = (msg) => setLogs((prev) => [...prev, `> ${msg}`]);

//   const stopPolling = () => {
//     if (pollIntervalRef.current) {
//       clearInterval(pollIntervalRef.current);
//       pollIntervalRef.current = null;
//     }
//   };

//   // Clean up polling on unmount
//   useEffect(() => {
//     return () => stopPolling();
//   }, []);

//   const fetchFineTuneStatus = async (datasetId) => {
//     try {
//       const response = await fetch(
//         `http://localhost:8000/api/v1/admin/finetune-status/${datasetId}`,
//         { credentials: "include" },
//       );

//       if (!response.ok) {
//         addLog(`Status fetch failed (${response.status}).`);
//         return;
//       }

//       const data = await response.json();

//       // Update truth from backend
//       if (data.status) setJobStatus(data.status);
//       if (typeof data.model !== "undefined") setJobModel(data.model);

//       // Append only new events
//       (data.events ?? []).forEach((msg) => addLog(`[OpenAI] ${msg}`));

//       // Stop polling on terminal status
//       if (TERMINAL_STATUSES.includes(data.status)) {
//         stopPolling();

//         if (data.status === "succeeded") {
//           addLog(
//             `Training succeeded. Model: ${data.model ?? "(not returned)"}`,
//           );
//         } else if (data.status === "failed") {
//           addLog("Training failed.");
//         } else if (data.status === "cancelled") {
//           addLog("Training cancelled.");
//         }
//       }
//     } catch (error) {
//       addLog(`Error fetching status: ${error.message}`);
//     }
//   };

//   const startPolling = (datasetId) => {
//     if (pollIntervalRef.current) return;

//     // Fetch immediately so UI updates right away
//     fetchFineTuneStatus(datasetId);

//     pollIntervalRef.current = setInterval(() => {
//       fetchFineTuneStatus(datasetId);
//     }, 30000);
//   };

//   const handleFileUpload = async (e) => {
//     const uploadedFile = e.target.files?.[0];
//     if (!uploadedFile) return;

//     setFile(uploadedFile);
//     setUploadState("processing");
//     addLog(`Uploading ${uploadedFile.name}...`);

//     try {
//       const formData = new FormData();
//       formData.append("file", uploadedFile);

//       const response = await fetch(
//         "http://localhost:8000/api/v1/admin/convert-mixed",
//         {
//           method: "POST",
//           credentials: "include",
//           body: formData,
//         },
//       );

//       if (!response.ok) {
//         throw new Error(`Failed to convert file: ${response.status}`);
//       }

//       const data = await response.json();
//       console.log("Conversion response:", data);

//       setUploadState("ready");
//       addLog("Backend: Excel parsed and converted to required format.");
//       addLog("Ready to begin OpenAI Fine-tuning.");
//       setDatasetId(data.id); // Store dataset ID for future status checks and actions
//     } catch (error) {
//       setUploadState("idle");
//       addLog(`Error processing file: ${error.message}`);
//     }
//   };

//   const startTuning = async () => {
//     if (!datasetId) {
//       addLog("No dataset available.");
//       return;
//     }

//     addLog("Requesting OpenAI job creation...");

//     try {
//       const response = await fetch(
//         `http://localhost:8000/api/v1/admin/start-finetune/${datasetId}`,
//         { method: "POST", credentials: "include" },
//       );

//       if (!response.ok) {
//         addLog(`Failed to start fine-tune (${response.status}).`);
//         return;
//       }

//       setJobStatus("queued");
//       startPolling(datasetId); //  pass state value
//     } catch (error) {
//       addLog(`Error starting fine-tune: ${error.message}`);
//     }
//   };

//   const handleAction = async (action) => {
//     if (action === "cancel") {
//       addLog("Sending cancellation request to OpenAI...");

//       try {
//         const response = await fetch(
//           `http://localhost:8000/api/v1/admin/cancel-finetune/${datasetId}`,
//           { method: "POST", credentials: "include" },
//         );

//         if (!response.ok) {
//           addLog(`Cancel request failed (${response.status}).`);
//           return;
//         }

//         // Do NOT stop polling immediately; wait until backend reports cancelled
//         startPolling(datasetId);
//       } catch (error) {
//         addLog(`Error cancelling job: ${error.message}`);
//       }
//     }
//   };

//   // Button logic derived from backend status
//   const canStart =
//     uploadState === "ready" &&
//     (jobStatus === "idle" || TERMINAL_STATUSES.includes(jobStatus));
//   const canCancel = RUNNING_STATUSES.includes(jobStatus);

//   return (
//     <div className="space-y-6">
//       <header>
//         <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
//           Model Training
//         </h2>
//         <p className="text-gray-600 dark:text-gray-400">
//           Upload training data and manage OpenAI job lifecycles.
//         </p>
//       </header>

//       <div className="grid gap-6">
//         {/* Configuration Card */}
//         <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
//           <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
//             <div>
//               <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
//                 Training Data (Excel)
//               </label>
//               <input
//                 type="file"
//                 accept=".xlsx, .xls"
//                 onChange={handleFileUpload}
//                 className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 dark:file:bg-gray-700 dark:file:text-gray-200"
//               />
//             </div>
//           </div>
//         </div>

//         {/* Execution Card */}
//         <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
//           <div className="flex items-center justify-between mb-6">
//             <div className="flex gap-3">
//               <button
//                 disabled={!canStart}
//                 onClick={startTuning}
//                 className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-all"
//               >
//                 Start Fine-Tuning
//               </button>

//               <button
//                 disabled={!canCancel}
//                 onClick={() => handleAction("cancel")}
//                 className="px-5 py-2.5 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-all"
//               >
//                 Cancel
//               </button>
//             </div>

//             <div className="text-right">
//               <span className="text-xs font-bold uppercase tracking-wider text-gray-400 block mb-1">
//                 Current Status
//               </span>
//               <span
//                 className={`text-sm font-bold ${
//                   jobStatus === "running"
//                     ? "text-green-500"
//                     : TERMINAL_STATUSES.includes(jobStatus)
//                       ? "text-blue-400"
//                       : "text-gray-500"
//                 }`}
//               >
//                 {(jobStatus || "idle").toUpperCase()}
//               </span>

//               {jobModel ? (
//                 <div className="text-xs text-gray-400 mt-1 break-all">
//                   Model: {jobModel}
//                 </div>
//               ) : null}
//             </div>
//           </div>

//           {/* Terminal */}
//           <div className="bg-gray-950 rounded-lg p-4 font-mono text-sm h-64 overflow-y-auto border border-gray-800 shadow-inner">
//             {logs.map((log, i) => (
//               <div key={i} className="text-gray-300 mb-1 leading-relaxed">
//                 <span className="text-gray-600 mr-2">
//                   [
//                   {new Date().toLocaleTimeString([], {
//                     hour: "2-digit",
//                     minute: "2-digit",
//                   })}
//                   ]
//                 </span>
//                 <span
//                   className={log.includes("[OpenAI]") ? "text-blue-400" : ""}
//                 >
//                   {log}
//                 </span>
//               </div>
//             ))}
//             <div ref={terminalEndRef} />
//           </div>
//         </div>
//       </div>

//       {/* Available Models */}
//       <div className="mt-6">
//         <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-4">
//           Available Fine-Tuned Models
//         </h2>
//         <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
//           {fineTunedModels.length > 0 ? (
//             <ul className="list-disc pl-5 space-y-1">
//               {fineTunedModels.map((model, index) => (
//                 <li key={index} className="text-gray-700 dark:text-gray-300">
//                   {model}
//                 </li>
//               ))}
//             </ul>
//           ) : (
//             <p className="text-gray-500 dark:text-gray-400 italic">
//               No fine-tuned models available.
//             </p>
//           )}
//         </div>
//       </div>
//     </div>
//   );
// };

// export default FineTuningView;

// --------------------------------------------------------new time stamps-------------------------------------------------------------

import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";

const TERMINAL_STATUSES = ["succeeded", "failed", "cancelled"];
const RUNNING_STATUSES = ["validating_files", "queued", "running"];

const FineTuningView = () => {
  const { fineTunedModels, setFineTunedModels } = useAuth();
  const [datasetId, setDatasetId] = useState(null);

  const [selectedModel, setSelectedModel] = useState("gpt-4o-mini-2024-07-18");
  const [file, setFile] = useState(null);

  const [uploadState, setUploadState] = useState("idle"); // idle, processing, ready

  const [jobStatus, setJobStatus] = useState("idle"); // idle | validating_files | queued | running | succeeded | failed | cancelled | paused (if you ever add)
  const [jobModel, setJobModel] = useState(null);

  const [logs, setLogs] = useState([
    {
      ts: Date.now(),
      text: "System initialized. Awaiting Excel upload...",
      type: "system",
    },
  ]);

  const pollIntervalRef = useRef(null);
  const terminalEndRef = useRef(null);
  const seenEventsRef = useRef(new Set());

  //   -------------------ensure unique events stored----------------

  const appendEvents = (events) => {
    events.forEach((msg) => {
      if (seenEventsRef.current.has(msg)) return;
      seenEventsRef.current.add(msg);
      addLog(msg, "openai");
    });
  };

  useEffect(() => {
    console.log("datasetId changed:", datasetId);
  }, [datasetId]);

  // Auto-scroll terminal
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const addLog = (text, type = "system") => {
    setLogs((prev) => [...prev, { ts: Date.now(), text, type }]);
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  console.log("fineTunedModels from context:", fineTunedModels);
  // Clean up polling on unmount
  useEffect(() => {
    return () => stopPolling();
  }, []);

  const fetchFineTuneStatus = async (datasetId) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/admin/finetune-status/${datasetId}`,
        { credentials: "include" },
      );

      if (!response.ok) {
        addLog(`Status fetch failed (${response.status}).`, "error");
        return;
      }

      const data = await response.json();

      // Update truth from backend
      if (data.status) setJobStatus(data.status);
      if (typeof data.model !== "undefined") setJobModel(data.model);

      // Append only new events
      //   (data.events ?? []).forEach((msg) => addLog(`[OpenAI] ${msg}`));
      appendEvents(data.events ?? []);

      // Stop polling on terminal status
      if (TERMINAL_STATUSES.includes(data.status)) {
        stopPolling();

        if (data.status === "succeeded") {
          addLog(
            `Training succeeded. Model: ${data.model ?? "(not returned)"}`,
          );
        } else if (data.status === "failed") {
          addLog("Training failed.", "error");
        } else if (data.status === "cancelled") {
          addLog("Training cancelled.", "error");
        }
      }
    } catch (error) {
      addLog(`Error fetching status: ${error.message}`, "error");
    }
  };

  const startPolling = (datasetId) => {
    if (pollIntervalRef.current) return;

    // Fetch immediately so UI updates right away
    fetchFineTuneStatus(datasetId);

    pollIntervalRef.current = setInterval(() => {
      fetchFineTuneStatus(datasetId);
    }, 30000);
  };

  const handleFileUpload = async (e) => {
    const uploadedFile = e.target.files?.[0];
    if (!uploadedFile) return;

    setFile(uploadedFile);
    setUploadState("processing");
    addLog(`Uploading ${uploadedFile.name}...`);

    try {
      const formData = new FormData();
      formData.append("file", uploadedFile);

      const response = await fetch(
        "http://localhost:8000/api/v1/admin/convert-mixed",
        {
          method: "POST",
          credentials: "include",
          body: formData,
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to convert file: ${response.status}`);
      }

      const data = await response.json();
      console.log("Conversion response:", data);

      setUploadState("ready");
      addLog("Backend: Excel parsed and converted to required format.");
      addLog("Ready to begin OpenAI Fine-tuning.");
      setDatasetId(data.id); // Store dataset ID for future status checks and actions
    } catch (error) {
      setUploadState("idle");
      addLog(`Error processing file: ${error.message}`, "error");
    }
  };

  const startTuning = async () => {
    if (!datasetId) {
      addLog("No dataset available.", "error");
      return;
    }

    addLog("Requesting OpenAI job creation...");

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/admin/start-finetune/${datasetId}`,
        { method: "POST", credentials: "include" },
      );

      if (!response.ok) {
        addLog(`Failed to start fine-tune (${response.status}).`);
        return;
      }

      setJobStatus("queued");
      startPolling(datasetId); //  pass state value
    } catch (error) {
      addLog(`Error starting fine-tune: ${error.message}`);
    }
  };

  const handleAction = async (action) => {
    if (action === "cancel") {
      addLog("Sending cancellation request to OpenAI...");

      try {
        const response = await fetch(
          `http://localhost:8000/api/v1/admin/cancel-finetune/${datasetId}`,
          { method: "POST", credentials: "include" },
        );

        if (!response.ok) {
          addLog(`Cancel request failed (${response.status}).`, "error");
          return;
        }

        // Do NOT stop polling immediately; wait until backend reports cancelled
        startPolling(datasetId);
      } catch (error) {
        addLog(`Error cancelling job: ${error.message}`, "error");
      }
    }
  };

  // Button logic derived from backend status
  const canStart =
    uploadState === "ready" &&
    (jobStatus === "idle" || TERMINAL_STATUSES.includes(jobStatus));
  const canCancel = RUNNING_STATUSES.includes(jobStatus);

  // -------------------activate model----------------

  const handleUseModel = async (datasetId) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/admin/activate-model/${datasetId}`,
        { method: "PUT", credentials: "include" },
      );
      if (response.ok) {
        console.log(`Model activated successfully.`);
      } else {
        console.error(`Failed to activate model (${response.status}).`);
      }
    } catch (error) {
      console.error("Error activating model:", error);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Model Training
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Upload training data and manage OpenAI job lifecycles.
        </p>
      </header>

      <div className="grid gap-6">
        {/* Configuration Card */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Training Data (Excel)
              </label>
              <input
                type="file"
                accept=".xlsx, .xls"
                onChange={handleFileUpload}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 hover:file:text-gray-500 file:text-blue-700 hover:file:bg-blue-100  dark:file:bg-gray-700 dark:file:text-gray-200"
              />
            </div>
          </div>
        </div>

        {/* Execution Card */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div className="flex gap-3">
              <button
                disabled={!canStart}
                onClick={startTuning}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-all"
              >
                Start Fine-Tuning
              </button>

              <button
                disabled={!canCancel}
                onClick={() => handleAction("cancel")}
                className="px-5 py-2.5 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-all"
              >
                Cancel
              </button>
            </div>

            <div className="text-right">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-400 block mb-1">
                Current Status
              </span>
              <span
                className={`text-sm font-bold ${
                  jobStatus === "running"
                    ? "text-green-500"
                    : TERMINAL_STATUSES.includes(jobStatus)
                      ? "text-blue-400"
                      : "text-gray-500"
                }`}
              >
                {(jobStatus || "idle").toUpperCase()}
              </span>

              {jobModel ? (
                <div className="text-xs text-gray-400 mt-1 break-all">
                  Model: {jobModel}
                </div>
              ) : null}
            </div>
          </div>

          {/* Terminal */}
          <div className="bg-gray-950 rounded-lg p-4 font-mono text-sm h-64 overflow-y-auto border border-gray-800 shadow-inner">
            {logs.map((log, i) => (
              <div key={i} className="text-gray-300 mb-1 leading-relaxed">
                <span className="text-gray-600 mr-2">
                  [
                  {new Date(log.ts).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  })}
                  ]
                </span>

                <span
                  className={
                    log.type === "openai"
                      ? "text-blue-400"
                      : log.type === "error"
                        ? "text-red-400"
                        : ""
                  }
                >
                  {"> "}
                  {log.text}
                </span>
              </div>
            ))}
            <div ref={terminalEndRef} />
          </div>
        </div>
      </div>

      {/* Available Models */}
      <div className="mt-6">
        <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-4">
          Available Fine-Tuned Models
        </h2>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
          {fineTunedModels.length > 0 ? (
            <ul className="list-disc pl-5 space-y-1">
              {fineTunedModels.map((model, index) => (
                <li
                  key={model.datasetId}
                  className="text-gray-700 dark:text-gray-300 flex items-center justify-between"
                >
                  {model.fineTunedModel}

                  <button
                    disabled={model.status}
                    className={`px-3 py-1 bg-blue-600  ${model.status ? "bg-blue-600 disabled" : "bg-slate-400 hover:bg-blue-700 cursor-pointer"} text-white rounded-lg font-medium transition-all`}
                    onClick={() => {
                      handleUseModel(model.datasetId);
                      setFineTunedModels((prev) =>
                        prev.map((m) =>
                          m.datasetId === model.datasetId
                            ? { ...m, status: true }
                            : { ...m, status: false },
                        ),
                      );
                    }}
                  >
                    {model.status ? "In Use" : "Use"}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 dark:text-gray-400 italic">
              No fine-tuned models available.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default FineTuningView;
