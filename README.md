# 🚀 AI Revenue Recovery Autopilot (RecoveryOS)

**Live Demo:** [RecoveryOS on AWS Elastic Beanstalk](http://recoveryos-backend-env.eba-cmkwyars.us-east-1.elasticbeanstalk.com/)

RecoveryOS is an autonomous Compound AI system designed to intelligently recover failed payments for fintech companies and SaaS platforms. Instead of relying on dumb "retry every 3 days" logic, RecoveryOS uses **Amazon Bedrock** to analyze the context of a failed payment, predict the probability of recovery, and autonomously execute the best strategy (Retry, Email, Payment Link, or Escalate).

Built specifically for the AWS Hackathon, this project demonstrates a highly governed, production-ready AI architecture.

---

## 🏗️ AWS Architecture & Tech Stack

This project was built entirely on native AWS infrastructure to ensure security, scalability, and compliance:

*   **Amazon Bedrock (Nova Micro):** Powers the core decision engine. It evaluates transaction history and failure reasons to generate human-readable explanations and draft personalized customer outreach emails.
*   **Amazon DynamoDB:** Implements an immutable *Single-Table Design* Audit Ledger. Every single AI decision, probability score, and policy constraint is streamed here for financial compliance.
*   **Amazon Verified Permissions / Cedar (Code Ready):** A zero-trust policy engine that prevents the AI from exceeding recovery budgets or spamming customers.
*   **AWS Elastic Beanstalk:** Hosts the unified Python (FastAPI) and React (Vite) application, cleanly handling complex Machine Learning dependencies.

---

## ✨ Key Features

1.  **Compound AI Workflow:** The system doesn't just use a single LLM call. It uses a structured pipeline: *Data Ingestion -> Risk Prediction (ML) -> Policy Guardrails -> Execution -> AI Explanation (Bedrock)*.
2.  **Strict Policy Guardrails:** The AI is strictly governed. If a transaction exceeds the maximum retry count, or if the recovery action costs more than the allowed budget, the policy engine intercepts and blocks the AI.
3.  **Immutable Audit Ledger:** Fintech requires extreme compliance. Every state change is written to DynamoDB, allowing human support agents to see exactly *why* the AI made a specific decision.
4.  **Unified Deployment:** To guarantee zero CORS issues and lightning-fast performance, the compiled React frontend is served statically through the FastAPI backend directly on AWS Elastic Beanstalk.

---

## 🚀 How to use the Demo

1.  Visit the [Live Demo Link](http://recoveryos-backend-env.eba-cmkwyars.us-east-1.elasticbeanstalk.com/).
2.  Click **Run Autopilot Batch** in the top right corner.
3.  The backend will simulate a batch of failed transactions, route them through the AI Policy Engine, and save the logs to DynamoDB.
4.  Click on the **Automated Recovery** tab at the bottom to view the transactions.
5.  Click on any transaction to see the **Amazon Bedrock** generated explanation and drafted email!

---

## 💻 Local Development

### Backend (Python/FastAPI)
```bash
cd recoveryos/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend (React/Vite)
```bash
cd recoveryos/frontend
npm install
npm run dev
```

*Note: You must have an AWS account with configured credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) and Amazon Nova Micro model access enabled in Bedrock to run locally.*
