import React from 'react';
import {BrowserRouter as Router, Route, Routes} from "react-router-dom";
import {CssBaseline} from "@mui/material";
import Dashboard from "./pages/Dashboard";

function App() {
  return (
    <Router>
      <CssBaseline /> {/* Define estilos globais do Material-UI */}
      <Routes>
        {/* Rota para a página principal */}
        <Route path="/" element={<Dashboard />} />
      </Routes>
    </Router>
  );
};

export default App;
