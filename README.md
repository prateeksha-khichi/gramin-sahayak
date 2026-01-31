# Gramin Sahayak

Gramin Sahayak is a Telegram-based AI assistant built to help rural users in India access basic financial information such as loan eligibility, government schemes, and fraud detection using simple Hindi language and voice interaction.

The goal of this project is to reduce dependency on middlemen and make financial information more accessible through a familiar interface like Telegram.

---

## Features

- Loan eligibility checking using a machine learning model
- Step-by-step conversational flow for collecting user inputs
- Fraud and fake loan scheme detection
- Government scheme information retrieval
- Voice-based interaction (speech-to-text)
- Document-based question answering using RAG
- Hindi and English language support
- PostgreSQL database for logging users and interactions

---

## Tech Stack

- Python
- FastAPI
- python-telegram-bot (async)
- Scikit-learn
- Sentence Transformers
- Retrieval Augmented Generation (RAG)
- PostgreSQL (NeonDB)
- ffmpeg for audio processing

---

## Project Structure

grahmin_sahayak_bot/
├── api/ # Backend APIs
├── bots/ # Telegram bot logic
├── services/ # Loan, fraud, and RAG services
├── rag/ # Embeddings and vector index
├── database/ # Database manager
├── models/ # Trained ML models
├── data/ # PDFs and datasets
├── utils/ # Helper utilities
├── build_index.py # Builds RAG index
└── requirements.txt


## Setup Instructions

### 1. Clone the repository

git clone https://github.com/your-username/gramin-sahayak.git
cd gramin-sahayak
2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate
3. Install dependencies
pip install -r requirements.txt
4. Install ffmpeg
Download ffmpeg from:
https://www.gyan.dev/ffmpeg/builds/

Add ffmpeg/bin to your system PATH and verify:

ffmpeg -version
Environment Variables
Create a .env file in the project root:

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GROQ_API_KEY=your_llm_api_key
DATABASE_URL=your_postgres_database_url
Running the Project
Build RAG index (run once or when PDFs change)
python build_index.py
Run Telegram bot
python bots/telegram_bot.py
Current Status
Core functionality is complete and working.
The project can be extended further with additional language support, external bank APIs, or deployment to cloud services.

Author
Prateeksha Khichi




## `.gitignore` (Minimal & Realistic)
venv/
__pycache__/
.env
*.log
*.ogg
*.wav
