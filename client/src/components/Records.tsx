import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom"; // Import useNavigate
import "./Records.css";
import { HiOutlineDocumentDownload, HiOutlineSearch } from "react-icons/hi";
import { FaEye } from "react-icons/fa6";
import { toast } from "react-toastify";

// Define the structure of a record
interface Record {
  id: number;
  first_name: string;
  last_name: string;
  age: number;
  clinical_history: string;
  disease: string;
  severity?: string;
}

const Records: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [records, setRecords] = useState<Record[]>([]); // Correctly typed state
  const navigate = useNavigate(); // Initialize navigate function

  useEffect(() => {
    const fetchRecords = async () => {
      const doctorId = sessionStorage.getItem("doctorId"); // Get doctor ID from sessionStorage
      if (!doctorId) {
        toast.error("You are not logged in.");
        return;
      }

      try {
        const response = await fetch(`http://127.0.0.1:5000/reports/${doctorId}`);
        if (response.ok) {
          const data: Record[] = await response.json(); // Explicitly type the fetched data
          setRecords(data); // Update the records state with the fetched data
        } else {
          toast.error("Failed to fetch records.");
        }
      } catch (error) {
        console.error("Error fetching records:", error);
        toast.error("Error fetching records.");
      }
    };

    fetchRecords();
  }, []);

  // Filtered records based on search term
  const filteredRecords = records.filter((record) =>
    `${record.first_name} ${record.last_name}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );

  return (
    <div className="records-wrapper">
      {/* Header */}
      <div className="records-header">
        <span>Patient Records</span>
        {/* Search Bar */}
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search by patient's name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button className="search-btn">
            <HiOutlineSearch />
          </button>
        </div>
      </div>
      <hr className="divider" />

      {/* Records List */}
      <div className="records-list">
        {filteredRecords.length > 0 ? (
          filteredRecords.map((record) => (
            <div key={record.id} className={`record-cell ${searchTerm ? "highlight" : ""}`}>
              {/* Left Section */}
              <div className="record-left">
                <div className="record-header">
                  <span className="record-name">
                    {record.first_name} {record.last_name}
                  </span>
                  {/* Status Badge */}
                  {/* Status Badge */}
                  {record.disease!="healthy" && 
                  <span className={`status-badge ${record.severity?.toLowerCase() || "unknown"}`}>
                    {record.severity || "Unknown"}
                  </span>}

                </div>
                <div className="record-details">
                  <p>
                    <strong>Age:</strong> {record.age} years
                  </p>
                  <p>
                    <strong>Clinical History:</strong> {record.clinical_history}
                  </p>
                  <p>
                    <strong>Disease:</strong> {record.disease}
                  </p>
                </div>
              </div>

              {/* Right Section */}
              <div className="record-right">
                {record.disease && (
                  <button
                    className="download-btn"
                    onClick={() => navigate(`/report/${record.id}`)} // Redirect to report page
                  >
                    <FaEye />
                    View Report
                  </button>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="no-records">No records found.</div>
        )}
      </div>
    </div>
  );
};

export default Records;
