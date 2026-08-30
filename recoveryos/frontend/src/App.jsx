import React from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import TransactionDetail from "./pages/TransactionDetail.jsx";
import PolicySettings from "./pages/PolicySettings.jsx";

export default function App() {
  const location = useLocation();
  
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-area">
          <Link to="/" className="brand">
            RecoveryOS
          </Link>
          <span className="brand-sub">AI Revenue Recovery Autopilot</span>
        </div>
        <nav className="top-nav">
          <Link to="/" className={location.pathname === "/" ? "active" : ""}>Dashboard</Link>
          <Link to="/policy" className={location.pathname === "/policy" ? "active" : ""}>Policy & Simulation</Link>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/policy" element={<PolicySettings />} />
          <Route path="/transaction/:id" element={<TransactionDetail />} />
        </Routes>
      </main>
    </div>
  );
}
