import {
  useEffect,
  useState,
  useCallback,
} from "react";

import { fetchVideos } from "./services/api.js";

import UploadPanel from "./components/UploadPanel.jsx";
import VideoList from "./components/VideoList.jsx";
import ChatPanel from "./components/ChatPanel.jsx";

import "./App.css";


const TERMINAL_STATUSES = [
  "ready",
  "failed",
];


export default function App() {
  const [videos, setVideos] = useState([]);

  const [selectedVideoId, setSelectedVideoId] =
    useState(null);

  const [error, setError] = useState("");


  const loadVideos = useCallback(async () => {
    try {
      const data = await fetchVideos();

      setVideos(data);
    } catch (err) {
      setError(
        err.message ||
        "Could not reach the backend."
      );
    }
  }, []);


  useEffect(() => {
    loadVideos();
  }, [loadVideos]);


  useEffect(() => {
    const hasActiveJob = videos.some(
      (video) =>
        !TERMINAL_STATUSES.includes(
          video.status
        )
    );

    if (!hasActiveJob) {
      return;
    }

    const interval = setInterval(
      loadVideos,
      3000
    );

    return () => {
      clearInterval(interval);
    };
  }, [videos, loadVideos]);


  function handleUploaded(video) {
    setError("");

    setVideos((prev) => [
      video,
      ...prev,
    ]);
  }


  function handleDeleted(videoId) {
    setVideos((prev) =>
      prev.filter(
        (video) =>
          video.id !== videoId
      )
    );

    if (selectedVideoId === videoId) {
      setSelectedVideoId(null);
    }

    setError("");
  }


  const selectedVideo =
    videos.find(
      (video) =>
        video.id === selectedVideoId
    ) || null;


  const hasReadyVideo =
    videos.some(
      (video) =>
        video.status === "ready"
    );


  const canAsk =
    selectedVideo
      ? selectedVideo.status === "ready"
      : hasReadyVideo;


  return (
    <div className="app-shell">

      <aside className="sidebar">

        <div className="brand">
          <h1>
            AI Teaching Assistant
          </h1>

          <p className="brand-tagline">
            Ask your lectures anything.
          </p>
        </div>


        <UploadPanel
          onUploaded={handleUploaded}
          onError={setError}
        />


        <nav className="video-nav">
          <VideoList
            videos={videos}
            selectedVideoId={
              selectedVideoId
            }
            onSelect={
              setSelectedVideoId
            }
            onDeleted={
              handleDeleted
            }
            onError={setError}
          />
        </nav>


        <div className="sidebar-footer">
          Built by <strong>Badri Sirimalla</strong>
        </div>

      </aside>


      <main className="main-pane">

        {error && (
          <p className="error-message top-error">
            {error}
          </p>
        )}


        <ChatPanel
          selectedVideo={
            selectedVideo
          }
          canAsk={canAsk}
        />

      </main>

    </div>
  );
}