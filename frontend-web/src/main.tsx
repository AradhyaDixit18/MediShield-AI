import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./index.css";
import App from "./App";
import Home from "./pages/Home";
import Assess from "./pages/Assess";
import Report from "./pages/Report";
import Dashboard from "./pages/Dashboard";
import About from "./pages/About";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<Home />} />
          <Route path="assess/:disease" element={<Assess />} />
          <Route path="report" element={<Report />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="about" element={<About />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>
);
