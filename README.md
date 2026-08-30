# RecoveryOS 🤖💰

**The Autonomous Financial Agent for Revenue Recovery**

[![Live Demo](https://img.shields.io/badge/Live_Demo-Vercel-black?style=for-the-badge&logo=vercel)](https://recovery-os-blue.vercel.app/)
[![Backend API](https://img.shields.io/badge/Backend-Render-purple?style=for-the-badge)](https://recoveryos-k0eu.onrender.com)

## 🚨 The Problem: The Silent Killer of SaaS
Every year, subscription businesses lose billions of dollars to **Involuntary Churn**—customers who want to keep using the product, but their payment fails because their card expired or they had insufficient funds. 

The industry standard to fix this is "Dunning": a generic, hardcoded loop that spams the customer with the exact same automated email every 3 days. It ignores the context of the failure, destroys the customer relationship, and recovers a fraction of the revenue.

## 🚀 The Solution: A Compound AI Agent
We realized that revenue recovery shouldn't be a generic loop. It should be a highly intelligent, calculated decision. 

**RecoveryOS** completely replaces dumb retries with predictive Machine Learning. It is a true Compound AI System that **Perceives** failures, **Reasons** through the math, and **Acts** autonomously.

### Core Architecture
1. **The Brain (Machine Learning):** Instead of `if/then` rules, RecoveryOS runs a trained **Random Forest Machine Learning** model. It analyzes the failure reason, customer history, and calculates the exact mathematical probability of recovering that money (Expected Value).
2. **The Guardrails (Deterministic Policy Engine):** To prevent "Rogue AI" behavior, a strict policy engine physically bars the AI from executing actions on high-value VIP accounts, pushing them to human operators.
3. **The Voice (Generative AI):** We integrated **Google Gemini 3.6** purely for human-in-the-loop tasks. It translates the AI's complex math into a plain-English explanation for support agents, and drafts hyper-personalized, white-glove recovery emails.

## 🌟 Key Features
* **Autonomous Processing:** Analyzes 10,000+ failed payment events in under a second.
* **The What-If Simulator:** A sandbox for CFOs. Safely tweak the AI's financial boundaries (like maximum discount allowed) and run synthetic simulations to forecast the financial impact *before* risking real company money.
* **VIP Escalation Queue:** High-value transactions are automatically flagged for manual review, complete with Gemini AI co-pilot drafting.
* **Razorpay Integration:** Dynamically generates real payment links for customers to seamlessly update their billing details.

## 🛠 Tech Stack
* **Frontend:** React, Vite, Vercel Serverless (API proxying)
* **Backend:** Python, FastAPI, Uvicorn, Hosted on Render
* **Machine Learning:** Scikit-Learn (Random Forest)
* **Generative AI:** Google Gemini 3.6 API

## 💻 Local Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/Adityarajsoni/RecoveryOs.git
cd RecoveryOs
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Activate virtual environment (Windows):
.\venv\Scripts\activate
# Install dependencies:
pip install -r requirements.txt
```
**Environment Variables:** Create a `.env` file in the `backend/` directory and add your Google Gemini API key:
`GEMINI_API_KEY="AIzaSy..."`

**Run Backend:**
```bash
uvicorn app.main:app --reload
```

### 3. Frontend Setup
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.
