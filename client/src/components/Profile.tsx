import React, { useState, useEffect } from "react";
import "./Profile.css";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { MdModeEditOutline } from "react-icons/md";
import {toast} from "react-toastify";

const Profile: React.FC = () => {
  const [profileImage, setProfileImage] = useState<string>("/default-image.png");
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    licenseNumber: "",
    dob: "",
    yearsOfExperience: "",
    clinicAddress: "",
    email: "",
    phone: "",
    specialization: "",
  });

  // Fetch doctor's details on component mount
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
            dob: data.dob,
            yearsOfExperience: data.years_of_experience,
            clinicAddress: data.clinic_address,
            email: data.email,
            phone: data.phone,
            specialization: data.specialization,
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

  // Handle image change
  // Handle image change
const [selectedFile, setSelectedFile] = useState<File | null>(null);

const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
  const file = event.target.files?.[0];
  if (file) {
    setSelectedFile(file); // Store file for upload
    const imageUrl = URL.createObjectURL(file);
    setProfileImage(imageUrl); // Show preview
  }
};


  // Handle form data change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({ ...prevData, [name]: value }));
  };

  // Save updated profile details
  // Save updated profile details
  const handleSave = async () => {
    const doctorId = sessionStorage.getItem("doctorId");
    if (!doctorId) {
      toast.error("You are not logged in.");
      return;
    }

    const formDataToSend = new FormData();

    // Append all text fields
    Object.entries(formData).forEach(([key, value]) => {
      formDataToSend.append(key, value);
    });

    // Append the profile image if it was updated
    const fileInput = document.getElementById("image-upload") as HTMLInputElement;
    if (fileInput?.files?.[0]) {
      formDataToSend.append("profile_image", fileInput.files[0]);
    }

    try {
      const response = await fetch(`http://127.0.0.1:5000/doctor/${doctorId}`, {
        method: "PUT",
        body: formDataToSend, // Send as FormData, no Content-Type header needed
      });

      if (response.ok) {
        toast.success("Profile updated successfully!");
      } else {
        toast.error("Failed to update profile.");
      }
    } catch (error) {
      console.error("Error updating profile:", error);
      toast.error("Error updating profile.");
    }
  };


  return (
    <div className="profile-wrapper">
      {/* Header */}
      <div className="profile-header">Doctor Profile</div>

      {/* Profile Container */}
      <div className="profile-container">
        {/* Personal Info */}
        <div className="profile-section">
          {/* Avatar */}
          <div className="avatar-container">
            <div className="avatar-wrapper">
              <img src={profileImage} alt="Doctor Avatar" />
              <button className="avatar-btn">
                <label htmlFor="image-upload" className="icon-edit">
                  <MdModeEditOutline />
                </label>
              </button>
              <input
                id="image-upload"
                type="file"
                accept="image/*"
                style={{ display: "none" }}
                onChange={handleImageChange}
              />
            </div>
          </div>

          {/* Form */}
          <div className="form">
            <div className="Name">
              <div className="input-group">
                <label>First Name</label>
                <input
                  type="text"
                  name="firstName"
                  placeholder="Enter first name"
                  value={formData.firstName}
                  onChange={handleInputChange}
                />
              </div>
              <div className="input-group">
                <label>Last Name</label>
                <input
                  type="text"
                  name="lastName"
                  placeholder="Enter last name"
                  value={formData.lastName}
                  onChange={handleInputChange}
                />
              </div>
            </div>
            <div className="input-group">
              <label>License Number</label>
              <input
                type="text"
                name="licenseNumber"
                placeholder="Enter license number"
                value={formData.licenseNumber}
                onChange={handleInputChange}
              />
            </div>
            

            <div className="Name">
              <div className="input-group">
              <label>Date of Birth</label>
              <input type="date" name="dob" value={formData.dob} onChange={handleInputChange} />
            </div>

             
              <div className="input-group">
                <label>Years of Experience</label>
                <input
                  type="number"
                  name="yearsOfExperience"
                  placeholder="e.g., 10"
                  value={formData.yearsOfExperience}
                  onChange={handleInputChange}
                />
              </div>
            </div>
            <div className="input-group">
              <label>Clinic Address</label>
              <input
                type="text"
                name="clinicAddress"
                placeholder="Enter clinic address"
                value={formData.clinicAddress}
                onChange={handleInputChange}
              />
            </div>
            <div className="Name">
              <div className="input-group">
                <label>Email</label>
                <input
                  type="email"
                  name="email"
                  placeholder="doctor@example.com"
                  value={formData.email}
                  onChange={handleInputChange}
                />
              </div>
              <div className="input-group">
                <label>Contact no.</label>
                <input
                  type="text"
                  name="phone"
                  placeholder="+91 XXXXXXXXXX"
                  value={formData.phone}
                  onChange={handleInputChange}
                />
              </div>
            </div>
            <div className="input-group">
                <label>Specialization</label>
                <input
                  type="text"
                  name="specialization"
                  placeholder="e.g., Cardiologist, Pediatrician"
                  value={formData.specialization}
                  onChange={handleInputChange}
                />
              </div>
          </div>
        </div>
        <hr className="divider" />
        {/* Buttons */}
        <div className="st-buttons">
          <button className="cancel">Cancel</button>
          <button className="save" onClick={handleSave}>
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default Profile;
