import React, { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { jsPDF } from "jspdf";
import html2canvas from "html2canvas";
import "./Report.css";
import { toast } from "react-toastify";


interface ReportData {
  doctor_name: string;
  doctor_email: string;
  doctor_phone: string;
  patient_name: string;
  patient_age: number;
  patient_gender: string;
  diagnosis_image: string;
  features: string[][];
  treatment_recommendations: string[];
  possible_cause: string[];
  blood_tests: string[];
  prescriptions: string[];
  disease: string[]
}

export const downloadPDF = async () => {
  const reportContainer = document.querySelector(".report-container") as HTMLElement | null;
  const downloadButton = document.querySelector(".download-button") as HTMLElement | null;
  const reportButton = document.querySelector(".report") as HTMLElement | null;

  if (!reportContainer) {
    toast.error("Unable to find the report section.");
    return;
  }

  try {
    if (downloadButton) downloadButton.style.display = "none"; // Hide button
    if (reportButton) reportButton.style.display = "none";

    // Capture the report content as an image
    const canvas = await html2canvas(reportContainer, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
    });

    const imgData = canvas.toDataURL("image/png");
    const pdfWidth = 210; // A4 width in mm
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

    // Set PDF height dynamically to fit all content
    const pdf = new jsPDF("p", "mm", [pdfWidth, pdfHeight]);

    // Add the captured report image to the PDF
    pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);

    // Load watermark image
    const watermarkImg = new Image();
    watermarkImg.src = "/logo.png";
    watermarkImg.crossOrigin = "anonymous"; // Ensure no CORS issues

    watermarkImg.onload = () => {
      const watermarkWidth = 100;
      const watermarkHeight = 100;
      const xPos = (pdfWidth - watermarkWidth) / 2;
      const yPos = (pdfHeight - watermarkHeight) / 2;

      // Create an off-screen canvas to modify the watermark opacity
      const tempCanvas = document.createElement("canvas");
      const ctx = tempCanvas.getContext("2d");

      tempCanvas.width = watermarkWidth;
      tempCanvas.height = watermarkHeight;

      if (ctx) {
        ctx.globalAlpha = 0.2; // Lower opacity further (0.05 - 0.1 recommended)
        ctx.drawImage(watermarkImg, 0, 0, watermarkWidth, watermarkHeight);
      }

      // Convert to image data
      const watermarkData = tempCanvas.toDataURL("image/png");

      // Add watermark **before** other elements to avoid covering text
      pdf.addImage(watermarkData, "PNG", xPos, yPos, watermarkWidth, watermarkHeight);

      pdf.save(`Medical_Report.pdf`);
    };

  } catch (error) {
    console.error("Error generating PDF:", error);
    toast.error("Failed to download the report. Please try again.");
  } finally {
    if (downloadButton) downloadButton.style.display = "block"; // Restore button
    if (reportButton) reportButton.style.display = "block";
  }
};


const generatePDF = async (): Promise<Blob | null> => {
  const reportContainer = document.querySelector(".report-container") as HTMLElement | null;
  const downloadButton = document.querySelector(".download-button") as HTMLElement | null;
  const reportButton = document.querySelector(".report") as HTMLElement | null;


  if (downloadButton) downloadButton.style.display = "block"; // Restore button
  if (reportButton) reportButton.style.display = "block";

  if (!reportContainer) {
    toast.error("Unable to find the report section.");
    return null;
  }

  try {
    const canvas = await html2canvas(reportContainer, { scale: 2, useCORS: true, allowTaint: true });
    const imgData = canvas.toDataURL("image/png");
    const pdfWidth = 210;
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
    const pdf = new jsPDF("p", "mm", [pdfWidth, pdfHeight]);

    pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);

    return new Blob([pdf.output("blob")], { type: "application/pdf" });

  } catch (error) {
    console.error("Error generating PDF:", error);
    toast.error("Failed to generate the report.");
    return null;
  } finally {
    if (downloadButton) downloadButton.style.display = "block"; // Restore button
    if (reportButton) reportButton.style.display = "block";
  }
};



const Report: React.FC = () => {
  const { record_id } = useParams<{ record_id: string }>();
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const reportRef = useRef<HTMLDivElement>(null);
  const [severity, setSeverity] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [reportText, setReportText] = useState("");
  const [includeAttachment, setIncludeAttachment] = useState(false);




  const sendEmail = async (record_id: string, reportText: string, includeAttachment: boolean) => {
    try {
      const response = await fetch("http://127.0.0.1:5000/send-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_text: reportText,
          include_attachment: includeAttachment,
          record_id
        }),
      });

      const data = await response.json();
      if (response.ok) {
        console.log("✅ Email sent successfully!");
      } else {
        console.error("❌ Email sending failed:", data.error);
      }
    } catch (error) {
      console.error("❌ Error sending email:", error);
    }
  };



  useEffect(() => {
    if (reportData?.features?.length) {
      // Find the feature with the maximum area
      const maxFeature = reportData.features.reduce((max, feature) =>
        parseFloat(feature[1]) > parseFloat(max[1]) ? feature : max
      );

      setSeverity(maxFeature[5]); // Extract severity
    }
  }, [reportData]);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:5000/view-report/${record_id}`);
        if (!response.ok) {
          throw new Error("Failed to fetch report data.");
        }
        const data: ReportData = await response.json();
        setReportData(data);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [record_id]);

  // console.log(reportData?.treatment_recommendations, reportData?.blood_tests, reportData?.possible_cause, reportData?.prescriptions)
  useEffect(() => {
    const uploadPDF = async () => {
      if (!reportData) return;

      const reportBlob = await generatePDF();
      if (!reportBlob) return;

      const formData = new FormData();
      formData.append("report_pdf", reportBlob, `Medical_Report_${record_id}.pdf`);
      formData.append("record_id", record_id as string);  // Include the record ID in the form data

      try {
        const response = await fetch("http://127.0.0.1:5000/upload-report", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Failed to upload report PDF.");
        }
      } catch (error) {
        console.error("Error uploading report:", error);
      }
    };

    uploadPDF();
  }, [reportData]);


  if (loading) return <div className="loading">Loading report...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!reportData) return <div className="error">Report not found.</div>;
  const isHealthy = reportData.disease.includes("healthy");
  console.log(reportData);

  return (
    <div className="report-container">
      <header className="report-header">
        <img src="/logo2.png " alt="Logo" className="logo" />
        <div className="doctor-info">
          <h1>{reportData.doctor_name}</h1>
          <p>{reportData.doctor_email}</p>
          <p>{reportData.doctor_phone}</p>
        </div>
        {/* <div className={`patient-status ${reportData.patient_status}`}>
          {reportData.patient_status.charAt(0).toUpperCase() + reportData.patient_status.slice(1)}
        </div> */}
        {!isHealthy &&
          <div className={severity ? `severity-status ${severity?.toLowerCase()}` : "moderate"}>
            {severity ? severity.charAt(0).toUpperCase() + severity.slice(1) : "Moderate"}
          </div>}

      </header>

      <hr className="divider" />

      <div className="report-body">
        <div className="text-content">
          <div className="floating-box">
            <h3>Patient Details </h3>
            <p>Name: {reportData.patient_name} </p>
            <div className="details">
              <p>Age: {reportData.patient_age} </p>
              <p>Gender: {reportData.patient_gender}</p>
            </div>
          </div>
          {isHealthy ? (
            <div className="healthy-message">
              <h3>Health Status</h3>
              <p>The patient is healthy. No further treatment or tests are required.</p>
            </div>
          ) : (
            <>
              <div className="output-section">
                <h3>Treatment Recommendations:</h3>
                <ul>
                  {reportData.treatment_recommendations &&
                    (Array.isArray(reportData.treatment_recommendations)
                      ? reportData.treatment_recommendations.map((item: string, index: number) => {
                        const [key, ...rest] = item.split(":");
                        return (
                          <li key={index}>
                            <strong>{key.trim()}:</strong>{" "}
                            <span>{rest.join(":").trim()}</span>
                          </li>
                        );
                      })
                      : Object.entries(reportData.treatment_recommendations).map(
                        ([key, value], index) => (
                          <li key={index}>
                            <strong>{key}:</strong>{" "}
                            <span>{String(value)}</span> {/* 👈 cast to string */}
                          </li>
                        )
                      ))}
                </ul>


              </div>

              <div className="output-section">
                <h3>Possible Causes:</h3>
                 <ul>
                  {reportData.possible_cause &&
                    (Array.isArray(reportData.possible_cause)
                      ? reportData.possible_cause.map((item: string, index: number) => {
                        const [key, ...rest] = item.split(":");
                        return (
                          <li key={index}>
                            <strong>{key.trim()}:</strong>{" "}
                            <span>{rest.join(":").trim()}</span>
                          </li>
                        );
                      })
                      : Object.entries(reportData.possible_cause).map(
                        ([key, value], index) => (
                          <li key={index}>
                            <strong>{key}:</strong>{" "}
                            <span>{String(value)}</span> {/* 👈 cast to string */}
                          </li>
                        )
                      ))}
                </ul>

              </div>

              <div className="output-section">
                <h3>Recommended Blood Tests:</h3>
                 <ul>
                  {reportData.blood_tests &&
                    (Array.isArray(reportData.blood_tests)
                      ? reportData.blood_tests.map((item: string, index: number) => {
                        const [key, ...rest] = item.split(":");
                        return (
                          <li key={index}>
                            <strong>{key.trim()}:</strong>{" "}
                            <span>{rest.join(":").trim()}</span>
                          </li>
                        );
                      })
                      : Object.entries(reportData.blood_tests).map(
                        ([key, value], index) => (
                          <li key={index}>
                            <strong>{key}:</strong>{" "}
                            <span>{String(value)}</span> {/* 👈 cast to string */}
                          </li>
                        )
                      ))}
                </ul>

              </div>

              <div className="output-section">
                <h3>Prescriptions:</h3>
                 <ul>
                  {reportData.prescriptions &&
                    (Array.isArray(reportData.prescriptions)
                      ? reportData.prescriptions.map((item: string, index: number) => {
                        const [key, ...rest] = item.split(":");
                        return (
                          <li key={index}>
                            <strong>{key.trim()}:</strong>{" "}
                            <span>{rest.join(":").trim()}</span>
                          </li>
                        );
                      })
                      : Object.entries(reportData.prescriptions).map(
                        ([key, value], index) => (
                          <li key={index}>
                            <strong>{key}:</strong>{" "}
                            <span>{String(value)}</span> {/* 👈 cast to string */}
                          </li>
                        )
                      ))}
                </ul>

              </div>
            </>
          )}
        </div>

        <div className="image-section">
          <img src={reportData.diagnosis_image} alt="Diagnosis" />

          {Array.isArray(reportData.features) && reportData.features.length > 0 && (
            <div className="detected-features">
              <h3>Detected Features:</h3>
              <ul>
                {reportData.features.map((feature, index) => (
                  <li key={`feature-${index}`}>
                    <strong>{feature[0]}: </strong>
                    Area = {feature[1]},
                    Size = {feature[2]}
                    {feature[3] !== "none" && `, Shape = ${feature[3]}`}
                    , Location = {feature[4]}
                  </li>
                ))}
              </ul>
            </div>
          )}

        </div>

      </div>

      {/* Signature and Download Button - Stays at Bottom Right */}
      <div className="signature-download-container">
        <div className="signature-section">
          <h2>Doctor's Signature</h2>
        </div>
        <div className="btns">
          <button className="report" onClick={() => setIsOpen(true)}>Report</button>
          <button className="download-button" onClick={downloadPDF}>
            Download Report
          </button>
        </div>

      </div>

      {/* Disclaimer - Stays at Bottom Center */}
      <div className="disclaimer">
        <p><strong>Disclaimer: The information provided is for informational purposes only and should not be considered a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider for personalized medical guidance.</strong></p>
      </div>
      {isOpen && (
        <div className="modal">
          <div className="modal-content">
            <h2>Submit Report</h2>
            <textarea
              value={reportText}
              onChange={(e) => setReportText(e.target.value)}
              placeholder="Describe the issue..."
              rows={4}
            />
            <div>
              <input
                type="checkbox"
                checked={includeAttachment}
                onChange={() => setIncludeAttachment(!includeAttachment)}
              />
              <label> Include attachment</label>
            </div>
            <div className="modal-footer">
              <button className="btn cancel" onClick={() => setIsOpen(false)}>Cancel</button>
              <button
                className="btn submit"
                onClick={() => sendEmail(record_id as string, reportText, includeAttachment)}
              >
                Submit
              </button>

            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Report;
