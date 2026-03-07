import AdminPanel from "./pages/Dashboard";
import FineTuningView from "./pages/FineTuning";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";

const App = () => {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/finetuning/:datasetId" element={<FineTuningView />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
