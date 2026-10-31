import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { HashRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Overview } from "./pages/Overview";
import { Tasks } from "./pages/Tasks";
import { Inbox } from "./pages/Inbox";
import { Decisions } from "./pages/Decisions";
import { Connect } from "./pages/Connect";
import { Evaluation } from "./pages/Evaluation";
import { Replay } from "./pages/Replay";
import { Setup } from "./pages/Setup";
import { Policy } from "./pages/Policy";
import { Review } from "./pages/Review";
import "./index.css";
import "./fonts.css";
import "./landing.css";

try { document.documentElement.classList.toggle("dark", localStorage.getItem("theme") === "dark"); } catch { /* Device storage is optional. */ }

createRoot(document.getElementById("root")!).render(<StrictMode><HashRouter><Layout><Routes>
  <Route path="/" element={<Overview />} />
  {["/tasks", "/delegate", "/agents"].map(path => <Route key={path} path={path} element={<Tasks />} />)}
  <Route path="/inbox" element={<Inbox />} />
  {["/activity", "/decisions"].map(path => <Route key={path} path={path} element={<Decisions />} />)}
  <Route path="/connect" element={<Connect />} />
  <Route path="/evaluation" element={<Evaluation />} />
  <Route path="/replay" element={<Replay />} />
  <Route path="/setup" element={<Setup />} />
  <Route path="/policy" element={<Policy />} />
  <Route path="/review" element={<Review />} />
  <Route path="*" element={<Tasks />} />
</Routes></Layout></HashRouter></StrictMode>);
