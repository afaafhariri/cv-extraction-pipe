"use client";
import { useState } from "react";
import axios from "axios";
import Footer from "@components/footer";
import Header from "@components/header";

export default function Home() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    cv: null,
  });
  const [fileName, setFileName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const FLASK_API_URL =
    process.env.NEXT_PUBLIC_FLASK_API_URL || "http://localhost:5000";

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === "phone" && !/^\d*$/.test(value) && value !== "") {
      return;
    }
    setFormData({ ...formData, [name]: value });
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];

    if (!file) {
      alert("Please upload a CV file.");
      return;
    }

    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];

    if (!allowedTypes.includes(file.type)) {
      alert("Only PDF or DOCX files are allowed.");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      alert("File size should be less than 5MB.");
      return;
    }

    setFormData({ ...formData, cv: file });
    setFileName(file.name);
  };

  const handleRemoveFile = () => {
    setFormData({ ...formData, cv: null });
    setFileName("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const emailValidation = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailValidation.test(formData.email)) {
      alert("Please enter a valid email address.");
      return;
    }

    if (!formData.cv) {
      alert("Please upload a CV.");
      return;
    }

    const formDataToSend = new FormData();
    formDataToSend.append("name", formData.name);
    formDataToSend.append("email", formData.email);
    formDataToSend.append("phone", formData.phone);
    formDataToSend.append("cv", formData.cv);

    setIsSubmitting(true);

    try {
      const response = await axios.post(
        `${FLASK_API_URL}/submit`,
        formDataToSend,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      if (response.status === 201) {
        alert("Application submitted successfully!");
        setFormData({
          name: "",
          email: "",
          phone: "",
          cv: null,
        });
        setFileName("");
      } else {
        alert(`Error: ${response.data.error}`);
      }
    } catch (error) {
      console.error("Submission error:", error);
      alert("Failed to submit application.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-grow flex justify-center items-center bg-[var(--background)]">
        <form
          onSubmit={handleSubmit}
          className="max-w-lg w-full p-6 border border-[var(--foreground)] space-y-4 "
        >
          <div className="flex space-x-4">
            <div className="flex-1">
              <label className="block font-medium text-[var(--foreground)]">
                Name
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="Enter your name"
                className="w-full p-2 border "
              />
            </div>
            <div className="flex-1">
              <label className="block font-medium [var(--foreground)]">
                Phone
              </label>
              <input
                type="text"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                required
                placeholder="Enter your phone"
                className="w-full p-2 border "
              />
            </div>
          </div>

          <div>
            <label className="block font-medium text-[var(--foreground)]">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="Enter your email"
              className="w-full p-2 border "
            />
          </div>

          <div>
            <label className="block font-medium text-[var(--foreground)]">
              Upload CV (PDF/DOCX)
            </label>
            <div className="flex items-center space-x-2">
              <label className="w-full p-2 border cursor-pointer flex items-center justify-between bg-[var(--background)]">
                <span className="text-[var(--foreground)]">
                  {fileName || "Choose a file..."}
                </span>
                <input
                  type="file"
                  accept=".pdf,.docx"
                  onChange={handleFileChange}
                  required
                  name="cv"
                  className="hidden"
                />
              </label>

              {fileName && (
                <button
                  type="button"
                  onClick={handleRemoveFile}
                  className="p-2 text-gray-700 bg-[var(--foreground)] border hover:bg-[var(--background)] hover:text-[var(--foreground)] transition-all duration-300"
                >
                  Remove
                </button>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full p-2 border cursor-pointer bg-[var(--background)] text-[var(--foreground)] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? "Submitting..." : "Submit Application"}
          </button>
        </form>
      </main>
      <Footer />
    </div>
  );
}
