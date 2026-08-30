import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client.js";

function formatINR(n) {
  if (n == null) return "—";
  return `₹${n.toLocaleString("en-IN")}`;
}

export default function TransactionDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [audit, setAudit] = useState([]);
  const [error, setError] = useState(null);
  
  // AI State
  const [explanation, setExplanation] = useState(null);
  const [explaining, setExplaining] = useState(false);
  const [draft, setDraft] = useState(null);
  const [drafting, setDrafting] = useState(false);

  useEffect(() => {
    Promise.all([
      api.getTransactionDetail(id),
      api.getAuditTrail(id).catch(() => [])
    ]).then(([txData, auditData]) => {
      setData(txData);
      setAudit(auditData);
    }).catch(e => setError(e.message));
  }, [id]);

  const handleExplain = async () => {
    setExplaining(true);
    try {
      const res = await api.explainDecision(id);
      setExplanation(res.explanation);
    } catch (e) {
      alert("Failed to generate AI explanation: " + e.message);
    } finally {
      setExplaining(false);
    }
  };

  const handleDraft = async () => {
    setDrafting(true);
    try {
      const res = await api.draftEmail(id);
      setDraft(res.draft);
    } catch (e) {
      alert("Failed to draft AI email: " + e.message);
    } finally {
      setDrafting(false);
    }
  };

  if (error) return <div className="error">{error}</div>;
  if (!data) return <div style={{padding: '2rem'}}>Loading...</div>;

  const { event, execution } = data;

  return (
    <div className="transaction-detail">
      <Link to="/" className="back-link">← Back to Dashboard</Link>
      <h2>Transaction {id}</h2>

      <section className="detail-grid">
        <div className="card form-card">
          <h3 style={{marginBottom: '1.5rem'}}>Event Details</h3>
          <div className="form-group row-group" style={{marginBottom: '1rem', paddingBottom: '1rem'}}>
            <div className="group-info"><label>Customer</label></div>
            <div style={{fontWeight: 500}}>{event.customer_id}</div>
          </div>
          <div className="form-group row-group" style={{marginBottom: '1rem', paddingBottom: '1rem'}}>
            <div className="group-info"><label>Amount</label></div>
            <div style={{fontWeight: 600, fontSize: '1.1rem'}}>{formatINR(event.amount)}</div>
          </div>
          <div className="form-group row-group" style={{marginBottom: '1rem', paddingBottom: '1rem'}}>
            <div className="group-info"><label>Payment Method</label></div>
            <div style={{color: 'var(--muted)'}}>{event.payment_method}</div>
          </div>
          <div className="form-group row-group" style={{marginBottom: '1rem', paddingBottom: '1rem'}}>
            <div className="group-info"><label>Failure Reason</label></div>
            <div style={{color: '#c2410c', fontWeight: 500, backgroundColor: '#fff7ed', padding: '0.25rem 0.75rem', borderRadius: '4px'}}>{event.failure_reason || "N/A"}</div>
          </div>
          <div className="form-group row-group" style={{marginBottom: 0, paddingBottom: 0, borderBottom: 'none'}}>
            <div className="group-info"><label>Timestamp</label></div>
            <div style={{color: 'var(--muted)', fontSize: '0.9rem'}}>{new Date(event.timestamp).toLocaleString()}</div>
          </div>
        </div>
        
        {execution && (
          <div className="card form-card" style={{background: '#f8fafc'}}>
            <h3 style={{marginBottom: '1.5rem'}}>Execution Result</h3>
            <div className="form-group row-group" style={{marginBottom: '1rem', paddingBottom: '1rem'}}>
              <div className="group-info"><label>Action Taken</label></div>
              <div style={{fontWeight: 600, color: 'var(--accent)'}}>{execution.action}</div>
            </div>
            <div className="form-group row-group" style={{marginBottom: '1rem', paddingBottom: '1rem'}}>
              <div className="group-info"><label>Simulated</label></div>
              <div>{execution.simulated ? "Yes" : "No"}</div>
            </div>
            <div className="form-group row-group" style={{marginBottom: '1rem', paddingBottom: '1rem'}}>
              <div className="group-info"><label>Success</label></div>
              <div>
                <span className={`status-badge ${execution.success ? 'recovered' : 'failed'}`}>
                  {execution.success ? "Yes" : "No"}
                </span>
              </div>
            </div>
            <div className="form-group row-group" style={{marginBottom: '1rem', paddingBottom: '1rem'}}>
              <div className="group-info"><label>Amount Recovered</label></div>
              <div style={{fontWeight: 600, fontSize: '1.1rem', color: execution.success ? '#16a34a' : 'inherit'}}>{formatINR(execution.amount_recovered)}</div>
            </div>
            <div className="form-group row-group" style={{marginBottom: 0, paddingBottom: 0, borderBottom: 'none'}}>
              <div className="group-info"><label>Detail</label></div>
              <div style={{color: 'var(--muted)', fontSize: '0.9rem', maxWidth: '200px', textAlign: 'right'}}>{execution.detail}</div>
            </div>
          </div>
        )}
      </section>

      <section className="detail-grid" style={{marginBottom: "2rem"}}>
        <div className="card ai-card">
          <h3 style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
            AI Decision Explanation
          </h3>
          
          {!explanation && !explaining && (
            <div style={{marginTop: '2rem', textAlign: 'center'}}>
              <p style={{color: 'var(--muted)', marginBottom: '1.5rem'}}>Generate a plain-English explanation of the ML model's decision.</p>
              <button className="run-btn cta-btn" style={{padding: '0.75rem 1.5rem', fontSize: '1rem'}} onClick={handleExplain}>
                Generate Explanation
              </button>
            </div>
          )}
          
          {explaining && (
            <div className="processing-state" style={{marginTop: '1.5rem', padding: '1.5rem 1rem'}}>
              <div className="processing-icon" style={{width: '40px', height: '40px', margin: '0 auto 1rem'}}><span className="spinner"></span></div>
              <h4 style={{margin: '0 0 0.5rem 0'}}>Analyzing Math...</h4>
              <p style={{fontSize: '0.85rem'}}>Gemini 1.5 Flash is interpreting the Random Forest decision tree.</p>
              <div className="progress-bar-container" style={{height: '4px', marginTop: '1rem'}}>
                <div className="progress-bar-fill"></div>
              </div>
            </div>
          )}

          {explanation && (
            <div className="ai-content" style={{marginTop: '1rem', background: '#f8fafc', padding: '1.5rem', borderRadius: '8px', borderLeft: '4px solid #2563eb'}}>
              <pre style={{whiteSpace: 'pre-wrap', fontFamily: 'inherit', margin: 0, lineHeight: 1.6}}>{explanation}</pre>
            </div>
          )}
        </div>

        <div className="card ai-card">
          <h3 style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            AI Customer Communication
          </h3>
          
          {!draft && !drafting && (
             <div style={{marginTop: '2rem', textAlign: 'center'}}>
               <p style={{color: 'var(--muted)', marginBottom: '1.5rem'}}>Draft a hyper-personalized, white-glove email to this VIP.</p>
               <button className="run-btn cta-btn" style={{padding: '0.75rem 1.5rem', fontSize: '1rem'}} onClick={handleDraft}>
                 Draft Customer Email
               </button>
             </div>
          )}

          {drafting && (
            <div className="processing-state" style={{marginTop: '1.5rem', padding: '1.5rem 1rem'}}>
              <div className="processing-icon" style={{width: '40px', height: '40px', margin: '0 auto 1rem'}}><span className="spinner"></span></div>
              <h4 style={{margin: '0 0 0.5rem 0'}}>Drafting Email...</h4>
              <p style={{fontSize: '0.85rem'}}>Generating a personalized email with payment links.</p>
              <div className="progress-bar-container" style={{height: '4px', marginTop: '1rem'}}>
                <div className="progress-bar-fill"></div>
              </div>
            </div>
          )}

          {draft && (
            <div className="ai-content" style={{marginTop: '1rem', background: '#f8fafc', padding: '1.5rem', borderRadius: '8px', borderLeft: '4px solid #2563eb'}}>
              <pre style={{whiteSpace: 'pre-wrap', fontFamily: 'inherit', margin: 0, lineHeight: 1.6}}>{draft}</pre>
            </div>
          )}
        </div>
      </section>

      {audit.length > 0 && (
        <section className="card why-action-panel">
          <h3>"Why this action?" — Engine Timeline</h3>
          <div className="timeline">
            {audit.map((a, i) => (
              <div key={i} className="timeline-event">
                <div className="timeline-time">{new Date(a.timestamp).toLocaleTimeString()}</div>
                <div className="timeline-content">
                  <strong>{a.event_type}</strong>
                  <p>{a.detail}</p>
                  {a.metadata && Object.keys(a.metadata).length > 0 && (
                    <pre>{JSON.stringify(a.metadata, null, 2)}</pre>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
