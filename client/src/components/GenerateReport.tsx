import React, { useState, useEffect } from "react";
import "./GenerateReport.css";
import { toast } from "react-toastify";
import { PiUploadSimpleBold } from "react-icons/pi";
import { RiAiGenerateText } from "react-icons/ri";
import { useLocation } from "react-router-dom";

const GenerateReport: React.FC = () => {
  // Allow medicalImage to be either a File or a URL string
  const [medicalImage, setMedicalImage] = useState<File | string | undefined>(undefined);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [patientAge, setPatientAge] = useState<number | undefined>(undefined);
  const [clinicalHistory, setClinicalHistory] = useState("");
  const [doctorId, setDoctorId] = useState<number>(1); // Assuming doctor is logged in and doctorId is 1
  const [loading, setLoading] = useState(false);
  const [patientGender, setPatientGender] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const location = useLocation();
  const patient = location.state?.patient;

  useEffect(() => {
    if (patient) {
      setFirstName(patient.fname);
      setLastName(patient.lname);
      setPatientAge(patient.age);
      setPatientGender(patient.gender);
      setClinicalHistory(patient.history);
      if (patient.image && typeof patient.image === "string") {
        setMedicalImage(patient.image);
      }
    }
  }, [patient]);

  // Type the event parameter as React.ChangeEvent<HTMLInputElement>
  const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      console.log("Selected file:", file); // Debugging step
      setMedicalImage(() => file); // Function-based state update to ensure React updates it properly
    } else {
      console.log("No file selected.");
    }
  };

  useEffect(() => {
    console.log("Updated medicalImage state:", medicalImage);
  }, [medicalImage]);



  // Type the event parameter as React.ChangeEvent<HTMLInputElement>
  const handleGenderChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPatientGender(event.target.value);
    console.log(`Selected Gender: ${event.target.value}`);
  };

  // Function to build the form data and send the report to the backend.
  // If a dcmValue is provided (from the modal), it is appended to the form.
  const sendReport = async (dcmValue: string | null = null) => {
    console.log("✅ Step 1: Preparing to send report...");

    if (!medicalImage || typeof medicalImage === "string") {
      console.error("❌ No valid file detected!");
      toast.error("Please upload a valid DICOM file.");
      return;
    }

    const formData = new FormData();
    formData.append("doctor_id", sessionStorage.getItem("doctorId") || "1");
    formData.append("first_name", firstName);
    formData.append("last_name", lastName);
    formData.append("age", String(patientAge));
    formData.append("clinical_history", clinicalHistory);
    formData.append("gender", patientGender);

    console.log("✅ Step 2: Appending medical image:", medicalImage.name);
    formData.append("medical_image", medicalImage);

    if (dcmValue !== null) {
      console.log("✅ Step 3: Appending DCM Value:", dcmValue);
      formData.append("dcm_value", dcmValue);
    }

    // **✅ Log final FormData before sending**
    console.log("✅ Step 4: Final FormData Contents:");
    // for (const [key, value] of formData.entries()) {
    //     console.log(`${key}:`, value);
    // }

    try {
      console.log("🚀 Step 5: Sending form data...");
      const response = await fetch("http://127.0.0.1:5000/report", {
        method: "POST",
        mode: 'cors',
        body: formData,
      });

      if (response.ok) {
        console.log("🎉 Report successfully sent!");
        const data = await response.json();
        window.location.href = `/report/${data.report_id}`;
      } else {
        console.error("❌ Failed to generate report. Server responded with:", response.status);
        toast.error("Failed to generate report.");
      }
    } catch (error) {
      console.error("❌ Error during fetch:", error);
      toast.error("Error generating report.");
    }
  };



  // When the user clicks "Generate Report"
  const handleSubmit = async () => {
    const sessionDoctorId = sessionStorage.getItem("doctorId");
    if (!sessionDoctorId) {
      toast.error("You are not logged in");
      return;
    }

    if (!firstName || !lastName || !patientAge || !clinicalHistory || !patientGender) {
      toast.error("Please fill all the details");
      return;
    }

    // Check if the uploaded file is a DICOM file.
    if (medicalImage && typeof medicalImage !== "string") {
      const fileName = medicalImage.name;
      const fileExt = fileName.split(".").pop()?.toLowerCase();
      if (fileExt === "dcm") {
        // Open the modal so the user can choose a value for the DICOM file.
        setIsModalOpen(true);
        console.log("ok")
        return; // Wait until a value is selected.
      }
    }
    setLoading(true);
    await sendReport();
    setLoading(false);
  };

  // Called when the user selects a value in the modal; value is a number.
  const handleDcmValue = async (value: string) => {
    setIsModalOpen(false);
    setLoading(true);
    await sendReport(value);
    setLoading(false);

  };

  return (
    <div className="generate-report-wrapper">
      {/* Header */}
      <div className="generate-report-header">Generate Medical Report</div>

      {/* Report Container */}
      <div className="generate-report-container">
        {/* Form Section */}
        <div className="input">
          <div className="form-section">
            <div className="input-group">
              <label>Patient's Name</label>
              <div className="full-name">
                <input
                  type="text"
                  placeholder="Enter patient's first name"
                  value={firstName}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFirstName(e.target.value)}
                />
                <input
                  type="text"
                  placeholder="Enter patient's last name"
                  value={lastName}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLastName(e.target.value)}
                />
              </div>
            </div>
            <div className="together">
              <div className="input-group">
                <label>Patient's Age</label>
                <input
                  type="number"
                  placeholder="Enter patient's age"
                  value={patientAge || ""}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPatientAge(Number(e.target.value))}
                />
              </div>

              <div className="input-group">
                <label style={{ marginBottom: "5px", fontSize: "14px" }}>
                  Patient's Sex
                </label>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  {["Male", "Female", "Other"].map((gender) => (
                    <button
                      key={gender}
                      onClick={() => setPatientGender(gender)}
                      style={{
                        padding: "8px 16px",
                        border: `1px solid ${patientGender === gender ? "#749ba1" : "#d1d1d1"}`,
                        backgroundColor: patientGender === gender ? "#749ba1" : "white",
                        color: patientGender === gender ? "white" : "black",
                        borderRadius: "8px",
                        cursor: "pointer",
                        fontSize: "14px",
                      }}
                    >
                      {gender}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="input-group">
              <label>Clinical History</label>
              <textarea
                placeholder="Enter clinical history or relevant details"
                value={clinicalHistory}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setClinicalHistory(e.target.value)}
                rows={4}
              ></textarea>
            </div>
          </div>

          {/* Image Upload Section */}
          <div className="image-upload-section">
            <div className="image-preview">
              {medicalImage ? (
                <>
                  <button className="cancel-image" onClick={() => setMedicalImage(undefined)}>
                    &times;
                  </button>
                  <img
                    src={
                      typeof medicalImage === "string"
                        ? medicalImage
                        : URL.createObjectURL(medicalImage)
                    }
                    alt="Uploaded Medical"
                  />
                </>
              ) : (
                <p>No image/dcm uploaded</p>
              )}
            </div>
            <button className="image-upload-btn">
              <label htmlFor="image-upload" className="icon-edit">
                <PiUploadSimpleBold /> Upload Medical Image
              </label>
            </button>
            <input
              id="image-upload"
              type="file"
              accept=".jpg,.jpeg,.dcm"
              style={{ display: "none" }}
              onChange={handleImageChange}
            />
          </div>
        </div>

        <hr className="divider" />

        <div className="buttons">
          <button className="save" onClick={handleSubmit} disabled={loading}>
            <RiAiGenerateText /> {loading ? "Generating..." : "Generate Report"}
          </button>
        </div>

        {loading && (
          <div className="loading-overlay">
            <div className="loader"></div>
            <div className="typing-container">
              <span id="typing-text">Preparing report......</span>
            </div>
          </div>
        )}
      </div>

      {/* Modal for DICOM Value Selection */}
      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <p>Please select:</p>
            <div className="modal-buttons">
              {["Middle", "Max Intensity", "Largest RoI", "Edges"].map((value) => (
                <button style={{ backgroundColor: "#74A7A9", color: "white" }}
                key={value} onClick={() => handleDcmValue(value)}>
                  {value}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GenerateReport;
