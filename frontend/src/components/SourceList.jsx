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


export default function SourceList({
  sources,
  onSourceClick,
}) {
  if (
    !sources ||
    sources.length === 0
  ) {
    return null;
  }


  return (
    <div className="source-list">

      <div className="source-tags">

        {sources.map((source, index) => {

          /*
           * Lecture title.
           */
          const title =
            source.title ||
            source.video_title ||
            "Lecture section";


          /*
           * Normalize timestamps to numbers.
           *
           * This handles both:
           *
           * 252
           *
           * and:
           *
           * "252"
           */
          const start =
            Number(source.start) || 0;

          const end =
            Number(source.end) || start;


          /*
           * Unique key for this evidence.
           */
          const sourceKey =
            source.chunk_id ||
            source.id ||
            `${source.video_id || title}-${start}-${end}-${index}`;


          return (
            <button
              type="button"
              className="source-tag"
              key={sourceKey}
              onClick={() => {

                if (!onSourceClick) {
                  return;
                }


                /*
                 * Send a normalized source object
                 * to ChatPanel.
                 */
                onSourceClick({
                  ...source,

                  title,

                  start,

                  end,
                });

              }}

              aria-label={
                `Watch ${title} from ` +
                `${formatTimestamp(start)} ` +
                `to ${formatTimestamp(end)}`
              }
            >

              {/* ============================== */}
              {/* Lecture title                   */}
              {/* ============================== */}

              <span className="source-tag-title">
                {title}
              </span>


              {/* ============================== */}
              {/* Timestamp                       */}
              {/* ============================== */}

              <span className="source-tag-time">

                {formatTimestamp(start)}

                {" – "}

                {formatTimestamp(end)}

              </span>

            </button>
          );
        })}

      </div>

    </div>
  );
}