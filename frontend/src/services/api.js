const API_BASE =
  import.meta.env.VITE_API_BASE ||
  "http://localhost:5000";


async function handleResponse(res) {
  let body = null;

  try {
    body = await res.json();
  } catch {
    // No JSON body.
  }

  if (!res.ok) {
    const message =
      (body && body.error) ||
      `Request failed (${res.status})`;

    throw new Error(message);
  }

  return body;
}


/*
 * Get all uploaded lectures.
 */
export async function fetchVideos() {
  const res = await fetch(
    `${API_BASE}/api/videos`
  );

  return handleResponse(res);
}


/*
 * Get processing status of one lecture.
 */
export async function fetchVideoStatus(videoId) {
  const res = await fetch(
    `${API_BASE}/api/videos/${videoId}/status`
  );

  return handleResponse(res);
}


/*
 * Returns the URL of the uploaded lecture video.
 */
export function getVideoUrl(videoId) {
  return `${API_BASE}/api/videos/${videoId}/file`;
}


/*
 * Upload a lecture.
 */
export async function uploadVideo(
  file,
  title,
  onProgress
) {
  const formData = new FormData();

  formData.append("file", file);

  if (title) {
    formData.append("title", title);
  }

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.open(
      "POST",
      `${API_BASE}/api/upload`
    );

    xhr.upload.onprogress = (event) => {
      if (
        onProgress &&
        event.lengthComputable
      ) {
        onProgress(
          Math.round(
            (event.loaded / event.total) * 100
          )
        );
      }
    };

    xhr.onload = () => {
      let body = null;

      try {
        body = JSON.parse(
          xhr.responseText
        );
      } catch {
        // Ignore invalid JSON.
      }

      if (
        xhr.status >= 200 &&
        xhr.status < 300
      ) {
        resolve(body);
      } else {
        reject(
          new Error(
            (body && body.error) ||
            `Upload failed (${xhr.status})`
          )
        );
      }
    };

    xhr.onerror = () => {
      reject(
        new Error(
          "Network error while uploading."
        )
      );
    };

    xhr.send(formData);
  });
}


/*
 * Delete a lecture.
 */
export async function deleteVideo(videoId) {
  const res = await fetch(
    `${API_BASE}/api/videos/${videoId}`,
    {
      method: "DELETE",
    }
  );

  return handleResponse(res);
}


/*
 * Ask a question about one lecture
 * or all lectures.
 */
export async function askQuestion(
  question,
  videoId
) {
  const res = await fetch(
    `${API_BASE}/api/ask`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
        video_id: videoId ?? null,
      }),
    }
  );

  return handleResponse(res);
}


/*
 * Backend health check.
 */
export async function fetchHealth() {
  const res = await fetch(
    `${API_BASE}/api/health`
  );

  return handleResponse(res);
}