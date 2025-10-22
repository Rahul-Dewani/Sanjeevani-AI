import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { MdDashboard } from "react-icons/md";
import { TbReportSearch } from "react-icons/tb";
import { RiFileHistoryLine } from "react-icons/ri";
import { MdOutlineForum } from "react-icons/md";
import { RxExit, RxHamburgerMenu } from "react-icons/rx";
import { PiSunBold } from "react-icons/pi";
import { IoMoon } from "react-icons/io5";
import "./Navbar.css";
import {toast} from "react-toastify";

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const [darkMode, setDarkMode] = useState(false);
  const [activeTab, setActiveTab] = useState("/dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false); // Controls sidebar visibility
  const [profileImage, setProfileImage] = useState<string>("/default-image.png");
  const logoutRef = useRef<HTMLDivElement>(null);
  const [logoutVisible, setLogoutVisible] = useState(false);
  const [formData, setFormData] = useState({
      firstName: "",
      lastName: "",
      licenseNumber: "",
      specialization: "",
      yearsOfExperience: "",
      clinicAddress: "",
      email: "",
      timezone: "GMT+05:30 - Indian Time",
    });

  const toggleTheme = () => {
    setDarkMode((prevMode) => !prevMode);
    document.body.classList.toggle("dark-mode", !darkMode);
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleNavigation = (path: string) => {
    setActiveTab(path);
    navigate(path);
    setSidebarOpen(false); // Close sidebar after navigation on small screens
  };

  const navigateToProfile = () => {
    setActiveTab("")
    navigate("/profile");
    setSidebarOpen(false); // Close sidebar
  };


  const handleLogoutClick = () => {
    setLogoutVisible((prev) => !prev); // Toggle the visibility of the log-out div
  };


  const handleOutsideClick = (event: MouseEvent) => {
    if (logoutRef.current && !logoutRef.current.contains(event.target as Node)) {
      setLogoutVisible(false); // Close log-out div if clicked outside
    }
  };

  useEffect(() => {
    document.addEventListener("mousedown", handleOutsideClick);
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
    };
  }, []);

  const handleLogout = () => {
    window.location.href = "http://127.0.0.1:3001/client/index.html";// Redirect to the home page (dummy link)
  };

  useEffect(() => {
      const doctorId = sessionStorage.getItem("doctorId"); // Get doctor ID from sessionStorage
      if (!doctorId) {
        toast.error("You are not logged in.");
        return;
      }
  
      const fetchDoctorDetails = async () => {
        try {
          const response = await fetch(`http://127.0.0.1:5000/doctor/${doctorId}`);
          if (response.ok) {
            const data = await response.json();
            setFormData({
              firstName: data.first_name,
              lastName: data.last_name,
              licenseNumber: data.license_number,
              specialization: data.specialization,
              yearsOfExperience: data.years_of_experience,
              clinicAddress: data.clinic_address,
              email: data.email,
              timezone: data.timezone || "GMT+05:30 - Indian Time",
            });
            if (data.profile_image) {
              setProfileImage(data.profile_image);
            }
          } else {
            toast.error("Failed to fetch doctor details.");
          }
        } catch (error) {
          console.error("Error fetching doctor details:", error);
          toast.error("Error fetching doctor details.");
        }
      };
  
      fetchDoctorDetails();
    }, []);
  
  return (
    <>
      {/* Hamburger Menu for small screens */}
      <div className="hamburger-menu" onClick={toggleSidebar}>
        <RxHamburgerMenu size={24} />
      </div>

      {/* Sidebar */}
      <div className={`sidebar ${darkMode ? "dark" : "light"} ${sidebarOpen ? "open" : ""}`}>
        {/* Header */}
        <div className="sidebar-header">
          <div className="logo" style={{width: "100%"}}>
            <img src="/logo.png" alt="Sanjeevani AI" />
            <h1>Sanjeevani AI</h1>
          </div>
          {/* <button aria-label="Toggle Theme" onClick={toggleTheme}>
            {darkMode ? <PiSunBold /> : <IoMoon />}
          </button> */}
        </div>

        {/* Menu */}
        <div className="menu">
          <div className="menu-section">
            <a
              className={`menu-item ${activeTab === "/dashboard" ? "active" : ""}`}
              onClick={() => handleNavigation("/dashboard")}
            >
              <span className="icon">
                <MdDashboard />
              </span>{" "}
              Dashboard
            </a>
            <a
              className={`menu-item ${activeTab === "/generate-report" ? "active" : ""}`}
              onClick={() => handleNavigation("/generate-report")}
            >
              <span className="icon">
                <TbReportSearch />
              </span>{" "}
              Generate Report
            </a>
            <a
              className={`menu-item ${activeTab === "/records" ? "active" : ""}`}
              onClick={() => handleNavigation("/records")}
            >
              <span className="icon">
                <RiFileHistoryLine />
              </span>{" "}
              Records
            </a>
            <a
              className={`menu-item ${activeTab === "/forum" ? "active" : ""}`}
              onClick={() => handleNavigation("/forum")}
            >
              <span className="icon">
                <MdOutlineForum />
              </span>{" "}
              Collaborative Forum
            </a>

          </div>
        </div>

        {/* Footer */}
        <div className="footer">
          <div className="profile" onClick={navigateToProfile}>
            <img src={profileImage} alt={formData.firstName} />
            <div className="profile-info">
              <p className="name">{formData.firstName} {formData.lastName ? formData.lastName[0].toUpperCase() + "." : ""}</p>
              <p>{formData.email}</p>
            </div>
            <RxExit className="exit-icon" onClick={(e) => {
          e.stopPropagation(); // Prevent triggering profile click
          handleLogoutClick();
        }} />
          </div>
          {logoutVisible && (
        <div className="logout-div" ref={logoutRef}>
          <button onClick={handleLogout}>Log Out</button>
        </div>
      )}
        </div>
      </div>
    </>
  );
};

export default Navbar;
