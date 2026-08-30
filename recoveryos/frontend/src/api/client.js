// Use Vercel Serverless proxy to bypass Chrome blocks
const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

export const api = {
  getDatasetSummary: () => request("/dataset/summary"),
  runRecoveryAutopilot: () => request("/recovery/run", { method: "POST" }),
  
  getLastResult: () => request("/recovery/last_result"),

  getTransactions: () => request("/recovery/transactions"),
  getTransactionDetail: (transactionId) => request(`/recovery/transaction/${transactionId}`),
  getAuditTrail: (transactionId) => request(`/recovery/audit/${transactionId}`),
  explainDecision: (id) => request(`/recovery/transaction/${id}/explain`, { method: "POST" }),
  draftEmail: (id) => request(`/recovery/transaction/${id}/draft_email`, { method: "POST" }),
  getPlaybook: () => request("/recovery/playbook"),
  getPolicy: () => request("/policy"),
  updatePolicy: (policy) =>
    request("/policy", { method: "PUT", body: JSON.stringify(policy) }),
  whatIf: (policy) =>
    request("/recovery/whatif", { method: "POST", body: JSON.stringify(policy) }),
};
