import { useState } from "react";
import { deleteVideo } from "../services/api.js";


const STATUS_LABELS = {
  uploaded: "Queued",
  extracting_audio: "Extracting audio…",
  transcribing: "Transcribing…",
  chunking: "Organizing chunks…",
  embedding: "Building index…",
  ready: "Ready",
  failed: "Failed",
};


function StatusDot({ status }) {
  const cls =
    status === "ready"
      ? "dot dot-ready"
      : status === "failed"
      ? "dot dot-failed"
      : "dot dot-processing";

  return (
    <span
      className={cls}
      aria-hidden="true"
    />
  );
}


export default function VideoList({
  videos,
  selectedVideoId,
  onSelect,
  onDeleted,
  onError,
}) {

  const [deletingId, setDeletingId] =
    useState(null);


  async function handleDelete(
    event,
    video
  ) {
    event.stopPropagation();

    const confirmed = window.confirm(
      `Are you sure you want to delete "${video.title}"?`
    );

    if (!confirmed) {
      return;
    }

    try {

      setDeletingId(video.id);

      await deleteVideo(video.id);

      if (onDeleted) {
        onDeleted(video.id);
      }

    } catch (err) {

      if (onError) {
        onError(
          err.message ||
          "Could not delete the video."
        );
      }

    } finally {

      setDeletingId(null);
    }
  }


  if (videos.length === 0) {
    return (
      <p className="empty-note">
        No lectures uploaded yet. Upload one
        to get started.
      </p>
    );
  }


  return (
    <ul className="video-list">

      <li>
        <button
          className={`video-item ${
            selectedVideoId === null
              ? "is-selected"
              : ""
          }`}
          onClick={() => onSelect(null)}
        >
          <span className="video-title">
            All lectures
          </span>
        </button>
      </li>


      {videos.map((video) => (

        <li key={video.id}>

          <div
            className={`video-item-wrapper ${
              selectedVideoId === video.id
                ? "is-selected"
                : ""
            }`}
          >

            <button
              className={`video-item ${
                selectedVideoId === video.id
                  ? "is-selected"
                  : ""
              }`}
              onClick={() =>
                onSelect(video.id)
              }
              title={
                video.status === "failed"
                  ? video.error_message
                  : STATUS_LABELS[
                      video.status
                    ]
              }
            >

              <StatusDot
                status={video.status}
              />

              <span className="video-title">
                {video.title}
              </span>

              {video.status !== "ready" && (
                <span className="video-status">
                  {STATUS_LABELS[
                    video.status
                  ] || video.status}
                </span>
              )}

            </button>


            <button
              type="button"
              className="delete-video-button"
              onClick={(event) =>
                handleDelete(
                  event,
                  video
                )
              }
              disabled={
                deletingId === video.id
              }
              title="Delete lecture"
              aria-label={`Delete ${video.title}`}
            >
              {deletingId === video.id
                ? "Deleting..."
                : "Delete"}
            </button>

          </div>

        </li>

      ))}

    </ul>
  );
}
