"""
Ollama service.

Responsibilities:
- Create embeddings using Ollama.
- Generate short factual answers using Ollama.
- Disable Qwen thinking output.
- Prevent reasoning/meta text from reaching the frontend.

Performance notes:
- Embeddings are processed in controlled batches.
- Transcript text is limited before embedding so excessively large
  chunks do not unnecessarily slow down the embedding model.
- The embedding model stays loaded using keep_alive.
"""

import re
import time

import requests

from config import Config


# =========================================================
# EXCEPTION
# =========================================================

class OllamaError(Exception):
    """Raised when Ollama cannot process a request."""
    pass


# =========================================================
# SESSION
# =========================================================

SESSION = requests.Session()


# =========================================================
# PERFORMANCE SETTINGS
# =========================================================

# Do not send an extremely large number of texts in one request.
# For your current project, 4 is a safe starting point.
EMBED_BATCH_SIZE = 4

# Maximum characters used for one chunk during embedding.
#
# This does NOT modify the stored transcript.
# It only limits the text sent to the embedding model.
#
# 2500 characters is normally more than enough for your merged
# transcript chunks while keeping embedding inference manageable.
EMBED_MAX_CHARS = 2500

# Embedding requests can be slow on CPU.
EMBED_TIMEOUT = 300

# Generation timeout.
GENERATE_TIMEOUT = 180


# =========================================================
# HELPERS
# =========================================================

def _ollama_url(endpoint: str) -> str:
    base_url = str(
        Config.OLLAMA_URL
    ).rstrip("/")

    return f"{base_url}{endpoint}"


def _prepare_embedding_text(text):
    """
    Prepare transcript text for embedding.

    Important:
    - The original transcript is NOT changed.
    - Only the text sent to the embedding model is limited.
    - Beginning and ending context are preserved when truncation
      is necessary.
    """

    text = str(text or "").strip()

    if not text:
        return ""

    if len(text) <= EMBED_MAX_CHARS:
        return text

    # Preserve both beginning and ending context.
    first_part = int(
        EMBED_MAX_CHARS * 0.70
    )

    last_part = (
        EMBED_MAX_CHARS
        - first_part
    )

    return (
        text[:first_part]
        + "\n...\n"
        + text[-last_part:]
    )


def _split_batches(items, batch_size):
    """
    Split a list into small batches.
    """

    for start in range(
        0,
        len(items),
        batch_size,
    ):
        yield items[
            start:start + batch_size
        ]


# =========================================================
# EMBEDDINGS
# =========================================================

def create_embedding(texts):
    """
    Create embeddings using Ollama.

    Supports:

        create_embedding(["text"])

        create_embedding(["text1", "text2"])

    Returns one embedding for every non-empty input text.

    The order of returned embeddings is preserved.
    """

    if isinstance(texts, str):
        texts = [texts]

    if not texts:
        return []

    # -----------------------------------------------------
    # Preserve the original ordering.
    #
    # We filter empty texts here because Ollama should not
    # receive empty embedding inputs.
    # -----------------------------------------------------

    prepared_texts = []

    for text in texts:

        text = str(
            text or ""
        ).strip()

        if not text:
            continue

        prepared = _prepare_embedding_text(
            text
        )

        if prepared:
            prepared_texts.append(
                prepared
            )

    if not prepared_texts:
        return []

    total_start = time.perf_counter()

    all_embeddings = []

    batches = list(
        _split_batches(
            prepared_texts,
            EMBED_BATCH_SIZE,
        )
    )

    print(
        "[OLLAMA] Starting embedding:"
    )

    print(
        f"[OLLAMA] Total texts : "
        f"{len(prepared_texts)}"
    )

    print(
        f"[OLLAMA] Batch size  : "
        f"{EMBED_BATCH_SIZE}"
    )

    print(
        f"[OLLAMA] Batches     : "
        f"{len(batches)}"
    )

    print(
        f"[OLLAMA] Model       : "
        f"{Config.OLLAMA_EMBED_MODEL}"
    )

    for batch_number, batch in enumerate(
        batches,
        start=1,
    ):

        batch_start = time.perf_counter()

        print(
            f"[OLLAMA] Embedding batch "
            f"{batch_number}/{len(batches)} "
            f"({len(batch)} text(s))..."
        )

        try:

            response = SESSION.post(
                _ollama_url(
                    "/api/embed"
                ),
                json={
                    "model": (
                        Config.OLLAMA_EMBED_MODEL
                    ),

                    "input": batch,

                    # Keep the embedding model loaded
                    # between batches.
                    "keep_alive": "10m",

                    # Do not silently discard long
                    # input. We already control the
                    # text length ourselves.
                    "truncate": False,
                },
                timeout=EMBED_TIMEOUT,
            )

        except requests.RequestException as exc:

            raise OllamaError(
                "Could not connect to Ollama "
                "while creating embeddings: "
                f"{exc}"
            ) from exc

        batch_elapsed = (
            time.perf_counter()
            - batch_start
        )

        if response.status_code != 200:

            raise OllamaError(
                "Ollama embedding error "
                f"{response.status_code}: "
                f"{response.text}"
            )

        try:

            data = response.json()

        except ValueError as exc:

            raise OllamaError(
                "Ollama returned invalid JSON "
                "for embeddings."
            ) from exc

        embeddings = data.get(
            "embeddings"
        )

        if not embeddings:

            raise OllamaError(
                "Ollama returned no embeddings "
                f"for batch {batch_number}."
            )

        # -------------------------------------------------
        # Verify batch count.
        # -------------------------------------------------

        if len(embeddings) != len(batch):

            raise OllamaError(
                "Ollama returned "
                f"{len(embeddings)} embeddings "
                f"for {len(batch)} inputs "
                f"in batch {batch_number}."
            )

        all_embeddings.extend(
            embeddings
        )

        print(
            f"[OLLAMA] Batch "
            f"{batch_number}/{len(batches)} "
            f"completed in "
            f"{batch_elapsed:.2f}s"
        )

    total_elapsed = (
        time.perf_counter()
        - total_start
    )

    print(
        f"[OLLAMA] Embedding completed: "
        f"{len(all_embeddings)} text(s) "
        f"in {total_elapsed:.2f}s"
    )

    return all_embeddings


# =========================================================
# THINKING REMOVAL
# =========================================================

def _remove_thinking(text):
    """
    Remove Qwen thinking/reasoning blocks.
    """

    if not text:
        return ""

    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<thinking>.*?</thinking>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<think>.*$",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<thinking>.*$",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    return text.strip()


# =========================================================
# ANSWER TAG
# =========================================================

def _extract_answer_tag(text):
    """
    Extract the answer from:

        <answer>
        ...
        </answer>
    """

    if not text:
        return ""

    match = re.search(
        r"<answer>\s*(.*?)\s*</answer>",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match:
        return match.group(1).strip()

    return ""


# =========================================================
# REMOVE REFERENCES
# =========================================================

def _remove_references(text):
    """
    Remove references/sources accidentally returned
    by the model.
    """

    if not text:
        return ""

    markers = [
        "### Referenced in",
        "Referenced in",
        "### References",
        "References:",
        "### Sources",
        "Sources:",
    ]

    lower = text.lower()

    positions = []

    for marker in markers:

        position = lower.find(
            marker.lower()
        )

        if position != -1:
            positions.append(
                position
            )

    if positions:
        text = text[
            :min(positions)
        ]

    return text.strip()


# =========================================================
# REMOVE ANSWER HEADINGS
# =========================================================

def _remove_answer_heading(text):
    """
    Remove things such as:

        Answer:
        Final answer:
        **Answer:**
    """

    if not text:
        return ""

    patterns = [
        r"^\s*\*\*answer\*\*\s*:?\s*",
        r"^\s*answer\s*:?\s*",
        r"^\s*\*\*final answer\*\*\s*:?\s*",
        r"^\s*final answer\s*:?\s*",
        r"^\s*final response\s*:?\s*",
    ]

    for pattern in patterns:

        text = re.sub(
            pattern,
            "",
            text,
            count=1,
            flags=re.IGNORECASE,
        )

    return text.strip()


# =========================================================
# REMOVE REASONING
# =========================================================

def _remove_reasoning(text):
    """
    Remove Qwen-style reasoning/meta text.
    """

    if not text:
        return ""

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return ""

    reasoning_starters = (
        "okay, so",
        "okay so",
        "so i",
        "so we",
        "hmm",
        "the user",
        "the question",
        "we are given",
        "we need to",
        "i need to",
        "i have to",
        "i should",
        "i must",
        "let me",
        "let's",
        "looking at",
        "according to",
        "the instructions",
        "the course material provided",
        "the course material states",
        "the answer should",
        "i will answer",
        "we must",
        "we should",
    )

    reasoning_found = False
    useful_lines = []

    for line in lines:

        lower = line.lower()

        if lower.startswith(
            reasoning_starters
        ):

            reasoning_found = True
            continue

        if (
            "i have to extract" in lower
            or "i need to extract" in lower
            or "we need to extract" in lower
            or "i should extract" in lower
            or "the key points are" in lower
        ):

            reasoning_found = True
            continue

        if reasoning_found:

            if lower in {
                "- it's a",
                "it's a",
                "it is a",
                "- it is a",
                "- it's",
            }:
                continue

            useful_lines.append(
                line
            )

        else:

            useful_lines.append(
                line
            )

    return "\n".join(
        useful_lines
    ).strip()


# =========================================================
# DETECT INCOMPLETE ANSWER
# =========================================================

def _is_incomplete_answer(text):
    """
    Detect obvious truncated/model-failure responses.
    """

    if not text:
        return True

    normalized = re.sub(
        r"\s+",
        " ",
        text.lower(),
    ).strip()

    bad_exact = {
        "it's a",
        "it is a",
        "it is",
        "it's",
        "the key points are",
        "the answer is",
        "i don't know",
        "i do not know",
        "not sure",
    }

    if normalized in bad_exact:
        return True

    if normalized.endswith(
        (
            " it's a",
            " it is a",
            " is a",
            " is an",
            " are",
            " means",
            " that",
            " which",
            " because",
            " and",
        )
    ):
        return True

    return False


# =========================================================
# FINAL CLEANING
# =========================================================

def _clean_generated_answer(text):
    """
    Convert raw Ollama output into a clean final answer.
    """

    if not text:
        return ""

    text = str(
        text
    ).strip()

    # -----------------------------------------------------
    # 1. Explicit answer tag
    # -----------------------------------------------------

    tagged = _extract_answer_tag(
        text
    )

    if tagged:
        text = tagged

    # -----------------------------------------------------
    # 2. Thinking
    # -----------------------------------------------------

    text = _remove_thinking(
        text
    )

    # -----------------------------------------------------
    # 3. References
    # -----------------------------------------------------

    text = _remove_references(
        text
    )

    # -----------------------------------------------------
    # 4. Reasoning
    # -----------------------------------------------------

    text = _remove_reasoning(
        text
    )

    # -----------------------------------------------------
    # 5. Headings
    # -----------------------------------------------------

    text = _remove_answer_heading(
        text
    )

    # -----------------------------------------------------
    # 6. Remove XML tags
    # -----------------------------------------------------

    text = re.sub(
        r"</?answer>",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # -----------------------------------------------------
    # 7. Remove obvious meta lines
    # -----------------------------------------------------

    bad_patterns = [
        r"^\s*i need to follow.*$",
        r"^\s*i must follow.*$",
        r"^\s*i should follow.*$",
        r"^\s*we must extract.*$",
        r"^\s*i need to extract.*$",
        r"^\s*let me analyze.*$",
        r"^\s*let's analyze.*$",
        r"^\s*the instructions say.*$",
        r"^\s*the instructions require.*$",
        r"^\s*i can only use.*$",
        r"^\s*i should only use.*$",
        r"^\s*i will answer.*$",
    ]

    cleaned_lines = []

    for line in text.splitlines():

        stripped = line.strip()

        if not stripped:
            continue

        remove = False

        for pattern in bad_patterns:

            if re.match(
                pattern,
                stripped,
                flags=re.IGNORECASE,
            ):

                remove = True
                break

        if not remove:
            cleaned_lines.append(
                stripped
            )

    text = "\n".join(
        cleaned_lines
    )

    # -----------------------------------------------------
    # 8. Normalize whitespace
    # -----------------------------------------------------

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    text = text.strip()

    # -----------------------------------------------------
    # 9. Reject incomplete output
    # -----------------------------------------------------

    if _is_incomplete_answer(
        text
    ):

        print(
            "[OLLAMA] Rejected incomplete "
            "model answer."
        )

        return ""

    return text


# =========================================================
# GENERATION
# =========================================================

def generate(prompt: str) -> str:
    """
    Generate a short factual answer using Ollama.

    Qwen thinking is disabled.
    """

    if not prompt:
        return ""

    start_time = time.perf_counter()

    generation_prompt = f"""
{prompt}

IMPORTANT OUTPUT RULE:

Return ONLY the final answer.

Do NOT explain your reasoning.
Do NOT analyze the question.
Do NOT say "Okay, so".
Do NOT say "the user is asking".
Do NOT say "I need to".
Do NOT say "we need to".
Do NOT describe what you are doing.

Return the answer in exactly this format:

<answer>your short final answer here</answer>
""".strip()

    payload = {
        "model": Config.OLLAMA_GENERATE_MODEL,

        "prompt": generation_prompt,

        # Disable Qwen thinking.
        "think": False,

        "stream": False,

        # Keep model loaded.
        "keep_alive": "10m",

        "options": {
            "temperature": 0.0,
            "top_p": 0.8,
            "repeat_penalty": 1.05,

            # Short factual answers.
            "num_predict": 120,

            # Small context for faster generation.
            "num_ctx": 2048,
        },
    }

    try:

        response = SESSION.post(
            _ollama_url(
                "/api/generate"
            ),
            json=payload,
            timeout=GENERATE_TIMEOUT,
        )

    except requests.RequestException as exc:

        raise OllamaError(
            f"Could not connect to Ollama: {exc}"
        ) from exc

    elapsed = (
        time.perf_counter()
        - start_time
    )

    if response.status_code != 200:

        raise OllamaError(
            f"Ollama generation error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    try:

        data = response.json()

    except ValueError as exc:

        raise OllamaError(
            "Ollama returned invalid JSON "
            "for generation."
        ) from exc

    # -----------------------------------------------------
    # NEVER use the thinking field.
    # -----------------------------------------------------

    thinking = data.get(
        "thinking",
        "",
    )

    if thinking:

        print(
            "[OLLAMA] Thinking field returned; "
            "ignored."
        )

    raw_answer = data.get(
        "response",
        "",
    )

    answer = _clean_generated_answer(
        raw_answer
    )

    print(
        f"[OLLAMA] Generation: "
        f"{elapsed:.2f}s"
    )

    if not answer:

        print(
            "[OLLAMA] Model returned no usable "
            "final answer."
        )

    return answer