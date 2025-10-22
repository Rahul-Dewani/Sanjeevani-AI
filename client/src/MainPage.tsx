import React from "react";
import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
// import { DoctorProvider } from "./context/DoctorContext";
import { ToastContainer, Slide } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import Navbar from "./components/Navbar";
import Dashboard from "./components/Dashboard";
import Profile from "./components/Profile";
import GenerateReport from "./components/GenerateReport";
import Forum from "./components/Forum";
import Records from "./components/Records";
import App from './SignInSide';
import Report from './components/Report';
import "./MainPage.css";

const MainPage: React.FC = () => {
  const location = useLocation(); // Hook to get the current route

  const shouldShowNavbar = location.pathname !== "/sign-in" && !location.pathname.startsWith("/report");


  return (
    // <DoctorProvider>
    <div className="app-container">
      {shouldShowNavbar && <Navbar />}
      {/* Main content (Profile, Dashboard, etc.) */}
      <div className={`main-content ${!shouldShowNavbar ? "no-navbar" : ""}`}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/generate-report" element={<GenerateReport />} />
          <Route path="/records" element={<Records />} />
          <Route path="/forum" element={<Forum />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/sign-in" element={<App />} />
          <Route path="/report/:record_id" element={<Report />} />
        </Routes>
      </div>
      <ToastContainer
        position="top-right"
        autoClose={5000} // ✅ Auto-close after 5s
        hideProgressBar={false}
        newestOnTop={true}
        closeOnClick
        pauseOnFocusLoss
        draggable
        pauseOnHover
        closeButton={false} // ❌ Remove close button
        transition={Slide} // ✅ Smooth sliding transition
        toastClassName="custom-toast"
      />

    </div>
    // </DoctorProvider>
  );
};

const AppRouter: React.FC = () => (
  <Router>
    <MainPage />
  </Router>
);

export default AppRouter;
