# 🎓 AI Teaching Assistant

An AI-powered lecture learning assistant that turns lecture videos into a searchable knowledge base and provides lecture-grounded answers using **Whisper, RAG, Ollama, and React**.

> Upload a lecture → Ask a question → Get an answer → See the lecture evidence → Jump directly to the relevant video timestamp.

---

## ✨ Features

- 🎥 Upload lecture videos
- 🎙️ Automatic Whisper transcription
- 🧩 Transcript chunking and processing
- 🧠 `bge-m3` semantic embeddings
- 🔎 Retrieval-Augmented Generation (RAG)
- 🤖 Local `qwen3:8b` answer generation
- 📚 Search across all lectures or a selected lecture
- 📌 Lecture-grounded answers
- ⏱️ Timestamped evidence
- ▶️ Click evidence to jump to the video
- 💬 Question and answer history
- 🚫 Refuses when relevant course material is not found
- 🖥️ Local AI inference through Ollama

---

## 🖼️ Application

### Question & Answer

```text
┌─────────────────────────────────────────────────────┐
│                 AI Teaching Assistant               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Asking about: Machine Learning                     │
│                                                     │
│  ┌─────────────────────────────────────┐  ┌─────┐   │
│  │ Ask anything about this lecture...  │  │ Ask │   │
│  └─────────────────────────────────────┘  └─────┘   │ 
│                                                     │
│  YOUR QUESTION                                      │
│  What is reinforcement learning?                    │
│                                                     │
│ ✦ AI ANSWER                                        │
│                                                     │
│  Reinforcement learning trains a machine to take    │
│  suitable actions and maximize reward in a          │
│  particular situation.                              │
│                                                     │
│  LECTURE EVIDENCE                                   │
│  [ ML Types  1:29 – 3:33 ]                          │
│                                                     │
│  VIDEO EVIDENCE                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │                                               │  │
│  │                 Lecture Video                 │  │
│  │                                               │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘

Clicking an evidence timestamp automatically moves the video player to the corresponding lecture section.

🧠 How It Works
                    Lecture Video
                         │
                         ▼
                    FFmpeg Audio
                         │
                         ▼
                      Whisper
                         │
                         ▼
                 Transcript Chunks
                         │
                         ▼
                     bge-m3
                         │
                         ▼
               embeddings.joblib
                         │
                         │
                  User Question
                         │
                         ▼
                    RAG Search
                         │
                         ▼
              Relevant Lecture Chunks
                         │
                         ▼
                   qwen3:8b
                         │
                         ▼
              Answer + Evidence
                         │
                         ▼
                 Video Timestamp

The system retrieves relevant lecture content before generating an answer.

This keeps the answer connected to the uploaded course material.

🏗️ Architecture
                    ┌──────────────────────┐
                    │       React          │
                    │      Frontend        │
                    └──────────┬───────────┘
                               │
                            REST API
                               │
                    ┌──────────▼───────────┐
                    │       Flask          │
                    │       Backend        │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        Video Pipeline       RAG          Ollama Service
              │                │                │
              ▼                ▼                ▼
           Whisper        bge-m3          qwen3:8b
              │                │
              └───────┬────────┘
                      ▼
              embeddings.joblib
                      │
                      ▼
                 SQLite / Files
🛠️ Tech Stack
Layer	Technology
Frontend	React + Vite
Backend	Flask
Language	Python / JavaScript
Database	SQLite
Speech-to-Text	Whisper
Embeddings	BAAI bge-m3
LLM	Ollama qwen3:8b
Video Processing	FFmpeg
Vector Store	embeddings.joblib
API	REST
📁 Project Structure
project/
│
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   │
│   ├── routes/
│   │   ├── upload.py
│   │   ├── videos.py
│   │   ├── chat.py
│   │   └── health.py
│   │
│   └── services/
│       ├── video.py
│       ├── ollama.py
│       ├── rag.py
│       └── pipeline.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatPanel.jsx
│   │   │   ├── SourceList.jsx
│   │   │   └── ...
│   │   │
│   │   ├── services/
│   │   │   └── api.js
│   │   │
│   │   └── ...
│   │
│   ├── package.json
│   └── ...
│
├── videos/
├── audios/
├── jsons/
├── newjsons/
│
├── embeddings.joblib
└── README.md
🤖 AI Models
Embedding
bge-m3

Used to create semantic embeddings for lecture chunks.

The existing embeddings.joblib knowledge base was created using bge-m3.

Generation
qwen3:8b

Used to generate answers from the retrieved lecture evidence.

Transcription
Whisper

The default development configuration uses:

WHISPER_MODEL=base
📚 RAG

The application uses Retrieval-Augmented Generation.

Question
   │
   ▼
Embedding / Retrieval
   │
   ▼
Relevant Lecture Chunks
   │
   ▼
Evidence Validation
   │
   ▼
Prompt
   │
   ▼
qwen3:8b
   │
   ▼
Grounded Answer
Lecture Filtering

Questions can be searched against:

All Lectures

or:

Selected Lecture

When a lecture is selected, retrieval uses its video_id to restrict the search.

📦 Existing Knowledge Base

The project includes:

embeddings.joblib

Current knowledge base:

8 lectures
7,252 chunks
1024-dimensional embeddings

The existing knowledge base does not need to be rebuilt just to run the application.

⚡ Incremental Indexing

New lectures are added incrementally.

Existing Embeddings
        +
New Lecture
        │
        ▼
New Chunks
        │
        ▼
bge-m3
        │
        ▼
Updated Knowledge Base

Existing lecture embeddings do not need to be regenerated when a new lecture is uploaded.

🚀 Getting Started
Prerequisites

Make sure the following are installed:

Python 3.10+
Node.js 18+
FFmpeg
Ollama

Verify:

python --version
node --version
npm --version
ffmpeg -version
ollama --version
1. Install Ollama Models
ollama pull bge-m3
ollama pull qwen3:8b

Verify:

ollama list
2. Backend Setup
cd project\backend

Create a virtual environment:

python -m venv venv

Activate it:

.\venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Create the environment file:

copy .env.example .env
3. Frontend Setup

Open another terminal:

cd project\frontend

Install dependencies:

npm install

Create the environment file:

copy .env.example .env

The frontend should use:

VITE_API_BASE=http://localhost:5000
▶️ Running the Application
Terminal 1 — Ollama
ollama serve
Terminal 2 — Backend
cd project\backend
.\venv\Scripts\Activate.ps1
python app.py

Backend:

http://localhost:5000
Terminal 3 — Frontend
cd project\frontend
npm run dev

Frontend:

http://localhost:5173

Open the frontend URL in your browser.

🎥 Using the Application
Upload a Lecture
Open the application.
Click Upload a lecture.
Select a video.
Enter a lecture title.
Wait for processing.
Wait until the status becomes Ready.

Processing:

Upload
  ↓
Audio Extraction
  ↓
Whisper
  ↓
Chunking
  ↓
Embedding
  ↓
Ready
Ask a Question

Select a lecture and ask something related to the course material.

Example:

What is reinforcement learning?

The application returns:

YOUR QUESTION
        ↓
AI ANSWER
        ↓
LECTURE EVIDENCE
        ↓
VIDEO EVIDENCE
Open Evidence

Click the lecture evidence:

ML Types
1:29 – 3:33

The video player will:

Scroll into view
      ↓
Load video
      ↓
Seek to 1:29
      ↓
Attempt playback
🛑 Unsupported Questions

If relevant information cannot be found in the uploaded course material, the application returns:

I couldn't find this information in the uploaded course material.

This prevents the system from intentionally answering questions without relevant lecture evidence.

🔌 API
Method	Endpoint	Description
GET	/api/health	Backend health
GET	/api/videos	List lectures
GET	/api/videos/<id>/status	Lecture processing status
GET	/api/videos/<id>/file	Stream lecture video
POST	/api/upload	Upload lecture
POST	/api/ask	Ask question
Ask Question
{
  "question": "What is reinforcement learning?",
  "video_id": 1
}

For all lectures:

{
  "question": "What is reinforcement learning?",
  "video_id": null
}
🔧 Configuration

Important backend settings include:

WHISPER_MODEL=base
FRONTEND_ORIGIN=http://localhost:5173

The application also uses configuration for:

Ollama URL
Embedding Model
Generation Model
Whisper Model
Similarity Threshold
Frontend Origin
🔄 From the Original Pipeline

The original project used standalone scripts:

video_to_mp3.py
mp3_to_json.py
merge_chunks.py
preprocess_json.py
process_incoming.py

Their processing logic has been integrated into the backend services:

backend/services/

The core models and processing approach remain based on the original pipeline.

🧩 Main Backend Services
File	Responsibility
video.py	Video processing and file operations
ollama.py	Ollama communication
rag.py	Retrieval and answer generation
pipeline.py	Lecture processing pipeline
🖥️ Main Frontend Components
File	Responsibility
ChatPanel.jsx	Questions, answers, evidence, video
SourceList.jsx	Evidence references and timestamps
services/api.js	Frontend API communication
🔐 Local-First AI

The core AI pipeline runs locally:

Whisper
   +
bge-m3
   +
qwen3:8b
   +
Ollama

No cloud LLM API is required for the core question-answering workflow.

📊 Current Status

Working

Supported
 Lecture video upload
 Audio extraction
 Whisper transcription
 Transcript processing
 Incremental embeddings
 RAG retrieval
 Lecture-specific retrieval
 Local Ollama inference
 Lecture-grounded answers
 Evidence timestamps
 Clickable evidence
 Video timestamp navigation
 React + Flask integration
🛣️ Future Improvements
 Transcript viewer
 Lecture bookmarks
 Quiz generation
 Flashcard generation
 Advanced transcript search
 Learning analytics
 Multiple course workspaces
 Persistent chat history
 User authentication
 Improved mobile interface
📸 Screenshots

Add your actual application screenshots here:

![Dashboard](screenshots/dashboard.png)

![Question Answer](screenshots/question-answer.png)

![Video Evidence](screenshots/video-evidence.png)

Recommended screenshots:

Main dashboard
Lecture upload
AI answer
Lecture evidence
Video evidence with timestamp
🧪 Example

Question

What is reinforcement learning?

Answer

Reinforcement learning trains a machine to take suitable actions and maximize reward in a particular situation. It uses an agent and an environment to produce actions and rewards.

Evidence

ML Types
1:29 – 3:33

The evidence can be clicked to jump directly to the corresponding section of the lecture.

📈 Project Flow
Upload Lecture
      │
      ▼
Extract Audio
      │
      ▼
Whisper
      │
      ▼
Create Chunks
      │
      ▼
Generate Embeddings
      │
      ▼
Store Knowledge
      │
      ▼
Ask Question
      │
      ▼
Retrieve Evidence
      │
      ▼
Generate Answer
      │
      ▼
Show Evidence
      │
      ▼
Jump to Video
🎯 Goal

The goal of this project is to make lecture learning more interactive and verifiable.

Instead of only receiving an AI-generated answer, the user can follow the complete path:

Question
   ↓
Answer
   ↓
Lecture Evidence
   ↓
Timestamp
   ↓
Original Video
📄 License

Add your preferred license here.

Example:

MIT License
👨‍💻 Badri Sirimalla

Your Name

AI Teaching Assistant
React • Flask • Whisper • RAG • Ollama