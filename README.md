# 🚀 MOSIP — Multi-Agent Orbital Sustainability Intelligence Platform

<p align="center">
  <b>AI-Powered Orbital Sustainability Intelligence System</b><br>
  Multi-Agent AI • RAG • Space Sustainability • Regulatory Intelligence
</p>

<p align="center">
  <a href="https://github.com/lucifernarayan/MOSIP">Repository</a> •
  <a href="https://mosip-1.vercel.app/">Live Demo</a>
</p>

---

## 🌍 Overview

MOSIP (Multi-Agent Orbital Sustainability Intelligence Platform) is an AI-powered platform designed to analyze satellites, evaluate orbital sustainability, assess regulatory compliance, forecast long-term risks, and generate actionable mitigation recommendations.

The platform combines real satellite datasets, regulatory knowledge bases, Retrieval-Augmented Generation (RAG), and a LangGraph-powered multi-agent architecture to support sustainable space operations.

---

## 🎯 Problem Statement

The rapid increase in satellite launches and orbital debris is creating significant challenges for:

* Collision avoidance
* Orbital congestion management
* Regulatory compliance
* Long-term sustainability
* End-of-life disposal planning

Today these analyses are fragmented across multiple tools and expert workflows.

MOSIP unifies them into a single AI-native decision-support platform.

---

## ✨ Key Features

* 🛰️ Real Satellite Intelligence
* 🤖 Multi-Agent AI Reasoning
* 📚 Regulatory RAG System
* ⚠️ Collision Risk Assessment
* 📈 Sustainability Scoring
* 🔍 ESA & IADC Compliance Analysis
* 📄 Automated Report Generation
* 🌐 Interactive Mission Dashboard
* 🚀 Real-Time Orbital Visualization

---

## 🏗️ Architecture

```text
User
 │
 ▼
Next.js Frontend
 │
 ▼
FastAPI Backend
 │
 ▼
LangGraph Orchestrator
 │
 ├── Orbital Analysis Agent
 ├── Collision Risk Agent
 ├── Compliance Agent
 ├── Sustainability Agent
 ├── Forecast Agent
 ├── Mitigation Agent
 └── Report Agent
 │
 ├── PostgreSQL
 ├── Qdrant
 └── Groq LLM
```

---

## 🤖 Multi-Agent System

| Agent                  | Responsibility                    |
| ---------------------- | --------------------------------- |
| Supervisor Agent       | Task orchestration and routing    |
| Orbital Analysis Agent | Orbit classification and analysis |
| Collision Risk Agent   | Collision probability assessment  |
| Compliance Agent       | ESA/IADC compliance evaluation    |
| Sustainability Agent   | Sustainability scoring            |
| Forecast Agent         | Long-term orbital prediction      |
| Mitigation Agent       | Risk mitigation recommendations   |
| Report Agent           | Executive and technical reports   |

---

## 📚 RAG Pipeline

```text
ESA Documents
IADC Guidelines
ISO Standards
       │
       ▼
Document Chunking
       │
       ▼
Embeddings (BAAI/bge-small-en-v1.5)
       │
       ▼
Qdrant Vector Database
       │
       ▼
Semantic Retrieval
       │
       ▼
Groq LLM
       │
       ▼
Grounded Regulatory Answers
```

---

## 🗄️ Data Infrastructure

### PostgreSQL

Stores:

* 15,680 Satellites
* 15,680 Risk Assessments
* 31,360 Orbital Records
* Conjunction Events
* Ingestion Logs

### Qdrant

Stores:

* ESA Regulations
* IADC Guidelines
* Regulatory Embeddings
* Compliance Knowledge Base

### Neo4j

Planned for future relationship analysis.

---

## 📊 Dataset Overview

| Metric           | Count  |
| ---------------- | ------ |
| Satellites       | 15,680 |
| Risk Assessments | 15,680 |
| Orbital Records  | 31,360 |

---

## 🛠️ Technology Stack

### Frontend

* Next.js
* TypeScript
* TailwindCSS
* Globe.gl
* Framer Motion

### Backend

* FastAPI
* Python

### AI Stack

* LangGraph
* LangChain
* Groq
* Llama 3.3 70B

### Databases

* PostgreSQL
* Qdrant

---

## 🚀 Local Setup

```bash
git clone https://github.com/lucifernarayan/MOSIP.git

cd MOSIP

pip install -r requirements.txt

cd frontend
npm install
```

### Backend

```bash
uvicorn backend.api.main:app --reload
```

### Frontend

```bash
cd frontend

npm run dev
```

---

## 🔐 Environment Variables

```env
GROQ_API_KEY=your_groq_key

POSTGRES_USER=mosip
POSTGRES_PASSWORD=your_password
POSTGRES_DB=mosip

QDRANT_HOST=localhost
QDRANT_PORT=6333
```

---

## 🌐 Live Demo

https://mosip-1.vercel.app/

---

## 📷 Screenshots

Add screenshots here:

```text
docs/images/dashboard.png
docs/images/satellite-analysis.png
docs/images/regulation-search.png
docs/images/report-generation.png
```

---

## 🔮 Future Roadmap

* Neo4j Relationship Intelligence
* Real-Time Space-Track Integration
* Orbital Propagation Engine
* Autonomous Mitigation Planning
* Multi-Constellation Analysis
* Sustainability Benchmarking

---

## 👥 Team

NITA Knights built MOSIP, a multi-agent AI platform transforming how satellites are monitored, assessed, and managed for long-term orbital sustainability.
---

## 📄 License

MIT License

---

## 🙏 Acknowledgements

* ESA
* IADC
* LangGraph
* LangChain
* Groq
* Qdrant
* FastAPI
* Next.js

---

<p align="center">
<b>Building the Future of Sustainable Space Operations 🚀</b>
</p>
