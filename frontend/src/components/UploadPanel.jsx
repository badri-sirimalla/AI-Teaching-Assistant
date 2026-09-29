import { useRef, useState } from "react";
import { uploadVideo } from "../services/api.js";

export default function UploadPanel({ onUploaded, onError }) {
  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  async function handleFileChange(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setProgress(0);

    try {
      const title = file.name.replace(/\.[^/.]+$/, "");
      const video = await uploadVideo(file, title, setProgress);
      onUploaded(video);
    } catch (err) {
      onError(err.message || "Upload failed.");
    } finally {
      setIsUploading(false);
      setProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div className="upload-panel">
      <input
        ref={fileInputRef}
        id="video-upload-input"
        type="file"
        accept="video/*"
        onChange={handleFileChange}
        disabled={isUploading}
        style={{ display: "none" }}
      />
      <label htmlFor="video-upload-input" className={`upload-button ${isUploading ? "is-busy" : ""}`}>
        {isUploading ? `Uploading… ${progress}%` : "+ Upload a lecture"}
      </label>
    </div>
  );
}
