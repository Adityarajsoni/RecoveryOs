import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";

function formatINR(n) {
  if (n == null) return "—";
  if (Math.abs(n) >= 100000) return `₹${(n / 100000).toFixed(1)}L`;
  return `₹${n.toLocaleString("en-IN")}`;
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [result, setResult] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch summary
    api.getDatasetSummary().then(setSummary).catch((e) => setError(e.message));
    
    // Attempt to restore previous run state
    api.getLastResult().then(res => {
      if (res) setResult(res);
    }).catch(() => {});
    
    api.getTransactions().then(txs => {
      if (txs && txs.length > 0) setTransactions(txs);
    }).catch(() => {});
  }, []);

  async function handleRun() {
    setRunning(true);
    setError(null);
    try {
      const res = await api.runRecoveryAutopilot();
      setResult(res);
      const txs = await api.getTransactions();
      setTransactions(txs);
    } catch (e) {
      setError(e.message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="dashboard">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 600 }}>Recovery Overview</h2>
        <button className="run-btn" onClick={handleRun} disabled={running}>
          {running ? (
            <span className="btn-content">
              <span className="spinner"></span> Running...
            </span>
          ) : (
            "Run Autopilot Batch"
          )}
        </button>
      </div>

      <section className="stat-grid">
        <StatCard label="Revenue at Risk" value={formatINR(summary?.revenue_at_risk)} />
        <StatCard
          label="Potentially Recoverable"
          value={result ? formatINR(result.revenue_at_risk * 0.6) : "—"}
        />
        <StatCard label="Recovery Attempts" value={result?.intervention_count ?? "—"} />
        <StatCard
          label="Successfully Recovered"
          value={result ? formatINR(result.revenue_recovered) : "—"}
        />
      </section>

      {running && (
        <section className="processing-state">
          <div className="processing-icon">
            <span className="spinner large-spinner"></span>
          </div>
          <h3>Analyzing 10,000 Payment Events...</h3>
          <p>Running Random Forest Risk Predictor & applying Policy Guardrails</p>
          <div className="progress-bar-container">
            <div className="progress-bar-fill"></div>
          </div>
        </section>
      )}

      {!running && !result && !error && (
        <section className="system-ready-state">
          <div className="ready-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
            </svg>
          </div>
          <h3>System Ready</h3>
          <p>The AI Engine is standing by to process {summary ? summary.at_risk_events.toLocaleString() : "..."} failed transactions.</p>
          <div className="ready-features">
            <div className="feature-pill">Random Forest Risk Scoring</div>
            <div className="feature-pill">Policy Engine Guardrails</div>
            <div className="feature-pill">Razorpay Link Generation</div>
          </div>
          <button className="run-btn cta-btn" onClick={handleRun}>
            Start Recovery Autopilot
          </button>
        </section>
      )}

      {error && <p className="error">{error}</p>}

      {!running && result && (
        <section className="funnel">
          <h3 style={{marginTop: 0, marginBottom: '1rem', fontSize: '1.1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem'}}>Recovery Funnel Analysis</h3>
          <div className="funnel-visual">
            <div className="funnel-step">
              <div className="step-val">{result.events_processed.toLocaleString()}</div>
              <div className="step-label">Total Events</div>
            </div>
            <div className="funnel-arrow">→</div>
            
            <div className="funnel-step">
              <div className="step-val">{result.at_risk_count.toLocaleString()}</div>
              <div className="step-label">At Risk</div>
            </div>
            <div className="funnel-arrow">→</div>
            
            <div className="funnel-step">
              <div className="step-val">{result.eligible_count.toLocaleString()}</div>
              <div className="step-label">Policy Eligible</div>
            </div>
            <div className="funnel-arrow">→</div>
            
            <div className="funnel-step">
              <div className="step-val">{result.intervention_count.toLocaleString()}</div>
              <div className="step-label">Interventions</div>
            </div>
            <div className="funnel-arrow">→</div>
            
            <div className="funnel-step success">
              <div className="step-val">{result.recovered_count.toLocaleString()}</div>
              <div className="step-label">Recovered</div>
            </div>
          </div>
          
          <div className="funnel-footer">
            <strong>Conversion / Recovery Rate:</strong> {(result.recovery_rate * 100).toFixed(1)}%
          </div>
        </section>
      )}

      {!running && transactions.length > 0 && (
        <TransactionTabs transactions={transactions} />
      )}
    </div>
  );
}

function TransactionTabs({ transactions }) {
  const [activeTab, setActiveTab] = useState('escalations');
  
  const escalations = transactions.filter(tx => tx.action_taken === "escalate");
  const automated = transactions.filter(tx => tx.action_taken !== "escalate");
  
  const displayList = activeTab === 'escalations' ? escalations : automated;

  return (
    <section className="transaction-tabs">
      <div className="tab-header" style={{display: 'flex', gap: '1rem', borderBottom: '1px solid var(--border)', marginBottom: '1rem', marginTop: '3rem'}}>
        <button 
          style={{background: 'none', border: 'none', borderBottom: activeTab === 'escalations' ? '2px solid var(--accent)' : '2px solid transparent', padding: '0.5rem 1rem', fontSize: '1.1rem', fontWeight: 600, color: activeTab === 'escalations' ? 'var(--text)' : 'var(--muted)', cursor: 'pointer'}}
          onClick={() => setActiveTab('escalations')}
        >
          VIP Escalations ({escalations.length})
        </button>
        <button 
          style={{background: 'none', border: 'none', borderBottom: activeTab === 'automated' ? '2px solid var(--accent)' : '2px solid transparent', padding: '0.5rem 1rem', fontSize: '1.1rem', fontWeight: 600, color: activeTab === 'automated' ? 'var(--text)' : 'var(--muted)', cursor: 'pointer'}}
          onClick={() => setActiveTab('automated')}
        >
          Automated Recovery ({automated.length})
        </button>
      </div>
      
      {displayList.length === 0 ? (
        <div className="empty-state" style={{padding: '2rem', textAlign: 'center', color: 'var(--muted)', border: '1px dashed var(--border)', borderRadius: '8px'}}>
          No transactions in this queue.
        </div>
      ) : (
        <div style={{maxHeight: '400px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '8px'}}>
          <table style={{margin: 0, border: 'none'}}>
            <thead style={{position: 'sticky', top: 0, background: '#f8fafc', zIndex: 1}}>
              <tr>
                <th>Transaction ID</th>
                <th>Customer ID</th>
                <th>Amount (INR)</th>
                <th>Action Taken</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {displayList.map(tx => (
                <tr key={tx.transaction_id}>
                  <td>
                    <Link to={`/transaction/${tx.transaction_id}`}>
                      {tx.transaction_id.slice(0, 8)}...
                    </Link>
                  </td>
                  <td>{tx.customer_id}</td>
                  <td>{formatINR(tx.amount)}</td>
                  <td>
                    <span style={{fontWeight: 500, color: tx.action_taken === 'escalate' ? '#c2410c' : 'inherit'}}>
                      {tx.action_taken}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${tx.status}`}>
                      {tx.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
