import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Devices from "./components/Devices";

const App = () => {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/devices/:roomId" element={<Devices />} />
            </Routes>
        </Router>
    );
};

export default App;
