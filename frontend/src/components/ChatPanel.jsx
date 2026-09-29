import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  askQuestion,
  getVideoUrl,
} from "../services/api.js";

import SourceList from "./SourceList.jsx";


function formatTimestamp(seconds) {
  const total = Math.max(
    0,
    Math.round(Number(seconds) || 0)
  );

  const mins = Math.floor(total / 60);
  const secs = total % 60;

  return `${mins}:${secs
    .toString()
    .padStart(2, "0")}`;
}


export default function ChatPanel({
  selectedVideo,
  canAsk,
}) {
  const [question, setQuestion] =
    useState("");

  const [entries, setEntries] =
    useState([]);

  const [isAsking, setIsAsking] =
    useState(false);

  const [error, setError] =
    useState("");

  const videoRef =
    useRef(null);

  const playerSectionRef =
    useRef(null);

  const [activeVideo, setActiveVideo] =
    useState(null);

  const [activeSource, setActiveSource] =
    useState(null);


  /*
   * Ask a question.
   */
  async function handleSubmit(event) {
    event.preventDefault();

    const trimmed =
      question.trim();

    if (
      !trimmed ||
      isAsking
    ) {
      return;
    }

    setIsAsking(true);
    setError("");

    try {
      const result =
        await askQuestion(
          trimmed,
          selectedVideo
            ? selectedVideo.id
            : null
        );

      /*
       * Newest answer stays at the top.
       */
      setEntries((prev) => [
        {
          question: trimmed,
          ...result,
        },
        ...prev,
      ]);

      setQuestion("");

      /*
       * Open the primary video returned
       * by the backend.
       */
      if (result.video?.video_id) {
        const nextVideo = {
          video_id:
            result.video.video_id,

          title:
            result.video.title ||
            "Lecture",

          start:
            Number(result.video.start) || 0,

          end:
            Number(result.video.end) || 0,
        };

        setActiveVideo(nextVideo);
        setActiveSource(nextVideo);
      } else {
        setActiveVideo(null);
        setActiveSource(null);
      }

    } catch (err) {
      setError(
        err.message ||
        "Something went wrong while asking that question."
      );
    } finally {
      setIsAsking(false);
    }
  }


  /*
   * Clear chat and video evidence.
   */
  function handleClearChat() {
    setEntries([]);
    setError("");

    setActiveVideo(null);
    setActiveSource(null);
  }


  /*
   * Open a lecture evidence source.
   *
   * IMPORTANT:
   * The source timestamp is converted to a
   * number here so the video always receives
   * the exact seek position.
   */
  function handleSourceClick(source) {
    if (!source?.video_id) {
      setError(
        "This reference is missing its video information."
      );

      return;
    }

    setError("");

    const startTime = Math.max(
      0,
      Number(source.start) || 0
    );

    const endTime = Math.max(
      startTime,
      Number(source.end) || 0
    );

    const nextVideo = {
      video_id:
        source.video_id,

      title:
        source.title ||
        "Lecture",

      start:
        startTime,

      end:
        endTime,
    };

    /*
     * Update the selected source.
     */
    setActiveVideo(nextVideo);
    setActiveSource(nextVideo);

    /*
     * Scroll to the player after React has
     * rendered/updated the player.
     */
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (
          playerSectionRef.current
        ) {
          playerSectionRef.current.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }
      });
    });
  }


  /*
   * Scroll to video whenever the active
   * evidence changes.
   */
  useEffect(() => {
    if (!activeVideo) {
      return;
    }

    const frame =
      requestAnimationFrame(() => {
        if (
          !playerSectionRef.current
        ) {
          return;
        }

        playerSectionRef.current.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      });

    return () => {
      cancelAnimationFrame(frame);
    };

  }, [
    activeVideo?.video_id,
    activeSource?.start,
  ]);


  /*
   * Seek video to the exact beginning
   * of the selected evidence.
   *
   * Example:
   *
   * 3:10 -> 190 seconds
   * 5:56 -> 356 seconds
   */
  useEffect(() => {
    if (!activeSource) {
      return;
    }

    const startTime = Math.max(
      0,
      Number(activeSource.start) || 0
    );

    let cancelled = false;


    function seekAndPlay() {
      const video =
        videoRef.current;

      if (
        !video ||
        cancelled
      ) {
        return;
      }

      try {
        /*
         * Stop whatever the video was
         * previously doing.
         */
        video.pause();

        /*
         * Force the video to the exact
         * source starting timestamp.
         */
        video.currentTime =
          startTime;

        /*
         * Try to start playing from there.
         */
        const playPromise =
          video.play();

        if (
          playPromise &&
          typeof playPromise.catch ===
            "function"
        ) {
          playPromise.catch(() => {
            /*
             * Browser autoplay may be blocked.
             * The video is still positioned at
             * the correct timestamp.
             */
          });
        }

      } catch {
        // Ignore browser seek errors.
      }
    }


    /*
     * The video element may still be loading.
     */
    const video =
      videoRef.current;

    if (!video) {
      return;
    }


    /*
     * If metadata is already loaded,
     * seek immediately.
     */
    if (video.readyState >= 1) {
      seekAndPlay();
    } else {
      /*
       * Otherwise wait until metadata exists.
       */
      video.addEventListener(
        "loadedmetadata",
        seekAndPlay,
        { once: true }
      );
    }


    /*
     * Also handle the case where the source
     * changes while the video is loading.
     */
    video.addEventListener(
      "canplay",
      seekAndPlay,
      { once: true }
    );


    return () => {
      cancelled = true;

      video.removeEventListener(
        "loadedmetadata",
        seekAndPlay
      );

      video.removeEventListener(
        "canplay",
        seekAndPlay
      );
    };

  }, [
    activeVideo?.video_id,
    activeSource?.start,
  ]);


  return (
    <div className="chat-panel">

      {/* ================================== */}
      {/* Lecture scope                       */}
      {/* ================================== */}

      <div className="chat-scope">

        <span>
          Asking about{" "}
        </span>

        <strong>
          {selectedVideo
            ? selectedVideo.title
            : "all lectures"}
        </strong>

      </div>


      {/* ================================== */}
      {/* Question form                       */}
      {/* ================================== */}

      <form
        className="ask-form"
        onSubmit={handleSubmit}
      >

        <div className="ask-input-wrap">

          <input
            type="text"
            value={question}
            onChange={(event) =>
              setQuestion(
                event.target.value
              )
            }
            placeholder={
              selectedVideo
                ? "Ask anything about this lecture..."
                : "Ask anything about your lectures..."
            }
            disabled={
              !canAsk ||
              isAsking
            }
            aria-label="Ask a question"
          />

        </div>


        <button
          type="submit"
          disabled={
            !canAsk ||
            isAsking ||
            !question.trim()
          }
          className="ask-button"
        >

          {isAsking ? (
            <>
              <span className="button-spinner" />
              Asking
            </>
          ) : (
            "Ask"
          )}

        </button>


        <button
          type="button"
          className="clear-chat-button"
          onClick={handleClearChat}
          disabled={
            entries.length === 0 ||
            isAsking
          }
        >
          Clear
        </button>

      </form>


      {/* ================================== */}
      {/* Cannot ask message                  */}
      {/* ================================== */}

      {!canAsk && (

        <div className="empty-state">

          <div className="empty-state-icon">
            +
          </div>

          <div>

            <strong>
              Start learning with your lecture
            </strong>

            <p>
              Upload and process a lecture
              before asking questions.
            </p>

          </div>

        </div>

      )}


      {/* ================================== */}
      {/* Error                               */}
      {/* ================================== */}

      {error && (

        <p className="error-message">
          {error}
        </p>

      )}


      {/* ================================== */}
      {/* Answers                             */}
      {/* ================================== */}

      <div className="entries">

        {entries.map(
          (entry, index) => (

            <article
              className="entry"
              key={index}
            >

              {/* ================================= */}
              {/* QUESTION                           */}
              {/* ================================= */}

              <div className="question-block">

                <div className="question-label">
                  YOUR QUESTION
                </div>

                <h2 className="entry-question">
                  {entry.question}
                </h2>

              </div>


              {/* ================================= */}
              {/* PRIMARY AI ANSWER                  */}
              {/* ================================= */}

              <div className="answer-card answer-card-primary">

                <div className="answer-card-header">

                  <div className="answer-badge">
                    ✦
                  </div>

                  <div className="answer-heading">

                    <div className="answer-label">
                      AI ANSWER
                    </div>

                    <div className="answer-context">
                      Based on your lecture
                    </div>

                  </div>

                </div>


                <div className="entry-answer">
                  {entry.answer}
                </div>

              </div>


              {/* ================================= */}
              {/* LECTURE EVIDENCE                   */}
              {/* ================================= */}

              {entry.sources?.length > 0 && (

                <div className="answer-evidence">

                  <div className="answer-evidence-header">

                    <div>

                      <div className="evidence-label">
                        LECTURE EVIDENCE
                      </div>

                      <h3>
                        Verify the answer from your lecture
                      </h3>

                    </div>

                    <span className="evidence-count">
                      {entry.sources.length}
                    </span>

                  </div>


                  <SourceList
                    sources={
                      entry.sources
                    }
                    onSourceClick={
                      handleSourceClick
                    }
                  />

                </div>

              )}

            </article>

          )
        )}

      </div>


      {/* ================================== */}
      {/* VIDEO EVIDENCE                      */}
      {/* ================================== */}

      {activeVideo && (

        <section
          ref={playerSectionRef}
          className="lecture-player-section"
        >

          {/* ================================= */}
          {/* Video header                       */}
          {/* ================================= */}

          <div className="lecture-player-header">

            <div className="lecture-player-heading">

              <div className="video-section-badge">
                VIDEO EVIDENCE
              </div>

              <h3 className="lecture-player-title">
                {activeSource?.title ||
                  activeVideo.title ||
                  "Lecture"}
              </h3>

              <p className="lecture-player-subtitle">
                Watch the exact part of the lecture
                referenced by the answer
              </p>

            </div>


            {activeSource && (

              <div className="lecture-player-time">

                <span className="time-label">
                  TIMESTAMP:
                </span>

                <span className="time-value">

                  {formatTimestamp(
                    activeSource.start
                  )}

                  {" – "}

                  {formatTimestamp(
                    activeSource.end
                  )}

                </span>

              </div>

            )}

          </div>


          {/* ================================= */}
          {/* Video                              */}
          {/* ================================= */}

          <div className="lecture-video-wrapper">

            <video
              key={`${activeVideo.video_id}-${activeSource?.start ?? 0}`}
              ref={videoRef}
              className="lecture-video"
              src={getVideoUrl(
                activeVideo.video_id
              )}
              controls
              preload="metadata"
              playsInline
            />

          </div>


          {/* ================================= */}
          {/* Player status                      */}
          {/* ================================= */}

          {activeSource && (

            <div className="lecture-player-note">

              <span className="player-status-dot" />

              <span>

                Playing from{" "}

                <strong>
                  {formatTimestamp(
                    activeSource.start
                  )}
                </strong>

                {" "}because this section supports
                the answer.

              </span>

            </div>

          )}

        </section>

      )}

    </div>
  );
}