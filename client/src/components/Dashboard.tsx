import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { useNavigate } from "react-router-dom";
import "./Dashboard.css";

const Dashboard: React.FC = () => {
  const [formData, setFormData] = useState({
    doctorName: "",
    totalPatients: 0,
    criticalPatients: [] as { id: number; name: string }[],
  });
  const [selectedPatient, setSelectedPatient] = useState<null | {
    fname: string;
    lname: string;
    age: number;
    gender: string;
    history: string;
    time: string;
    image: string;
  }>(null);

  const navigate = useNavigate();

  useEffect(() => {
    const doctorId = sessionStorage.getItem("doctorId");
    if (!doctorId) {
      toast.error("You are not logged in.");
      return;
    }

    const abortController = new AbortController();
    const fetchDoctorDetails = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:5000/dashboard/${doctorId}`, {
          signal: abortController.signal,
        });

        if (response.ok) {
          const data = await response.json();
          setFormData({
            doctorName: data.doctor_name,
            totalPatients: data.total_patients,
            criticalPatients: data.critical_patients || [],
          });
        } else {
          toast.error("Failed to fetch doctor details.");
        }
      } catch (error) {
        if (error instanceof Error && error.name !== "AbortError") {
          console.error("Error fetching doctor details:", error);
          toast.error("Error fetching doctor details.");
        }
      }
    };

    fetchDoctorDetails();

    return () => abortController.abort();
  }, []);

  // Appointments Data
  const appointments = [
    // { fname: "Rahul", lname: "Dewani", age: 32, gender: "Male", history: "Diabetes", time: "09:00 AM", image: "./brain-disease.jpg" }, // Sindhi 👳‍♂️
    // { fname: "Palak", lname: "Rajani", age: 29, gender: "Female", history: "Thyroid", time: "09:30 AM", image: "./liver-tumor-disease.jpg" }, // Sindhi 👩‍⚕️
    // { fname: "Amit", lname: "Gokhale", age: 40, gender: "Male", history: "Hypertension", time: "10:00 AM", image: "./liver.jpg" }, // Brahmin 🕉️
    // { fname: "Shruti", lname: "Joshi", age: 27, gender: "Female", history: "Asthma", time: "10:30 AM", image: "./liver.jpg" }, // Brahmin 🕉️
    // { fname: "Yash", lname: "Kulkarni", age: 38, gender: "Male", history: "Obesity", time: "11:00 AM", image: "./liver.jpg" }, // Maratha 
    { fname: "Vaishali", lname: "Chhangani", age: 45, gender: "Female", history: "Arthritis", time: "11:30 AM", image: "./liver-tumor-disease.jpg" }, // Maratha 
    { fname: "Rohit", lname: "Sawant", age: 30, gender: "Male", history: "Heart Disease", time: "12:00 PM", image: "./brain-disease.jpg" }, // Konkani 🌊
    { fname: "Snehal", lname: "Patil", age: 42, gender: "Female", history: "Diabetes", time: "12:30 PM", image: "./kidney-disease.jpg" }, // Maratha
    { fname: "Vikram", lname: "Deshmukh", age: 50, gender: "Male", history: "Liver Issues", time: "01:00 PM", image: "./chest-disease.jpg" }, 
    { fname: "Meenal", lname: "Bhave", age: 36, gender: "Female", history: "PCOS", time: "01:30 PM", image: "./eye-disease.jpg" } 
];


  return (
    <div className="dashboard">
      {/* Top Section */}
      <div className="top-section">
        <div className="welcome-banner">
          <h1>Welcome, Dr. {formData.doctorName}!</h1>
        </div>
        <div className="dashboard-top">
          <div className="metric-card">
            <img className="icon" src="/patient.png" alt="Patient Icon" />
            <div className="details">
              <h2>Total Patients</h2>
              <p>{formData.totalPatients}</p>
            </div>
          </div>
          <div className="metric-card">
            <img className="icon" src="/appointment.png" alt="Appointment Icon" />
            <div className="details">
              <h2>Today's Appointments</h2>
              <p>{appointments.length}</p>
            </div>
          </div>
          <div className="metric-card">
            <img className="icon" src="/pending.png" alt="Pending Reports Icon" />
            <div className="details">
              <h2>Pending Reports</h2>
              <p>3</p>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section */}
      <div className="bottom-section">
        {/* Critical Patients */}
        <div className="critical-patients">
          <h2>Critical Patients</h2>
          <ul>
            {formData.criticalPatients.map((patient) => (
              <li key={patient.id}>
                <p>{patient.name}</p>
                <button onClick={() => navigate(`/report/${patient.id}`)}>View Report</button>
              </li>
            ))}
          </ul>
        </div>

        {/* Today's Appointments */}
        <div className="appointments">
          <h2>Today's Appointments</h2>
          <ul>
            {appointments.map((appointment, index) => (
              <li key={index}>
                <div className="appointment-details">
                  <p>
                    <strong>{appointment.fname} {appointment.lname}</strong> <br />
                    Age: {appointment.age}, Gender: {appointment.gender} <br />
                    History: {appointment.history} <br />
                    <span style={{paddingTop:"2px"}}>Time: {appointment.time}</span>
                  </p>
                </div>
                <button onClick={() => setSelectedPatient(appointment)}>View Image</button>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Modal Popup */}
      {selectedPatient && (
  <div className="modal-overlay" onClick={() => setSelectedPatient(null)}>
    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
      <img
        src={selectedPatient.image}
        alt={selectedPatient.fname}
        className="patient-image"
      />
      <div className="btns">
      <button onClick={() => navigate("/generate-report", { state: { patient: selectedPatient } })}>
          Generate Report
        </button>
        
        <button
          onClick={() => {
            const link = document.createElement("a");
            link.href = selectedPatient.image;
            link.download = `${selectedPatient.fname}-image.jpg`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          }}
        >
          Download Image
        </button>
        <button onClick={() => setSelectedPatient(null)}>Close</button>
      </div>
    </div>
  </div>
)}

    </div>
  );
};

export default Dashboard;
