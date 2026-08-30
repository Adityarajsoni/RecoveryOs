import React, { useEffect, useState } from "react";
import { api } from "../api/client.js";

function formatINR(n) {
  if (n == null) return "—";
  return `₹${n.toLocaleString("en-IN")}`;
}

export default function PolicySettings() {
  const [policy, setPolicy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // What-If state
  const [simulationResult, setSimulationResult] = useState(null);
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    api.getPolicy()
      .then(p => {
        setPolicy(p);
        setLoading(false);
      })
      .catch(e => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  const handleChange = (field, value) => {
    setPolicy(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.updatePolicy(policy);
      alert("Policy updated successfully!");
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleSimulate = async () => {
    setSimulating(true);
    setError(null);
    setSimulationResult(null);
    try {
      const res = await api.whatIf(policy);
      setSimulationResult(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setSimulating(false);
    }
  };

  if (loading) return <div style={{padding: '2rem'}}>Loading policy...</div>;
  if (!policy) return <div className="error">{error}</div>;

  return (
    <div className="dashboard policy-settings">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 600 }}>Policy Guardrails</h2>
          <p className="subtitle" style={{ margin: '0.25rem 0 0 0' }}>Configure the rules of engagement for the AI Recovery Engine.</p>
        </div>
        <button className="run-btn save-btn" onClick={handleSave} disabled={saving}>
          {saving ? (
            <span className="btn-content"><span className="spinner"></span> Saving...</span>
          ) : "Save Changes"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="detail-grid" style={{ gridTemplateColumns: '1.2fr 1fr' }}>
        
        {/* Left Side: Settings Form */}
        <div className="card form-card">
          <h3>Financial Boundaries</h3>
          
          <div className="form-group row-group">
            <div className="group-info">
              <label>Max Recovery Budget</label>
              <small>Total budget allowed for all interventions combined.</small>
            </div>
            <div className="input-wrap">
              <span className="input-prefix">₹</span>
              <input 
                type="number" 
                value={policy.max_recovery_budget} 
                onChange={e => handleChange("max_recovery_budget", parseFloat(e.target.value))}
              />
            </div>
          </div>

          <div className="form-group row-group">
            <div className="group-info">
              <label>Human Approval Threshold</label>
              <small>Transactions above this amount will pause for manual review.</small>
            </div>
            <div className="input-wrap">
              <span className="input-prefix">₹</span>
              <input 
                type="number" 
                value={policy.human_approval_above} 
                onChange={e => handleChange("human_approval_above", parseFloat(e.target.value))}
              />
            </div>
          </div>

          <h3 style={{ marginTop: '2rem' }}>Engagement Limits</h3>

          <div className="form-group row-group">
            <div className="group-info">
              <label>Max Retries</label>
              <small>Max times to silently retry a direct debit per customer.</small>
            </div>
            <div className="input-wrap">
              <input 
                type="number" 
                value={policy.max_retries} 
                onChange={e => handleChange("max_retries", parseInt(e.target.value))}
              />
            </div>
          </div>

          <div className="form-group row-group">
            <div className="group-info">
              <label>Max Contact Attempts</label>
              <small>Max times to email or SMS a customer.</small>
            </div>
            <div className="input-wrap">
              <input 
                type="number" 
                value={policy.max_customer_contact_attempts} 
                onChange={e => handleChange("max_customer_contact_attempts", parseInt(e.target.value))}
              />
            </div>
          </div>
          
          <h3 style={{ marginTop: '2rem' }}>Automation Features</h3>

          <div className="form-group toggle-group">
            <div className="group-info">
              <label>Auto-generate Payment Links</label>
              <small>Allow AI to create and send Razorpay payment links.</small>
            </div>
            <label className="toggle-switch">
              <input 
                type="checkbox" 
                checked={policy.auto_generate_payment_links} 
                onChange={e => handleChange("auto_generate_payment_links", e.target.checked)}
              />
              <span className="slider"></span>
            </label>
          </div>

          <div className="form-group toggle-group">
            <div className="group-info">
              <label>Auto-send Notifications</label>
              <small>Allow AI to email customers via GenAI drafts.</small>
            </div>
            <label className="toggle-switch">
              <input 
                type="checkbox" 
                checked={policy.auto_send_notifications} 
                onChange={e => handleChange("auto_send_notifications", e.target.checked)}
              />
              <span className="slider"></span>
            </label>
          </div>

        </div>

        {/* Right Side: Simulator */}
        <div className="card simulator-card">
          <div className="simulator-header">
            <div>
              <h3>What-If Simulator</h3>
              <p className="muted" style={{fontSize: '0.85rem', margin: 0}}>Test these settings safely against the baseline.</p>
            </div>
            <button className="run-btn simulate-btn" onClick={handleSimulate} disabled={simulating}>
              {simulating ? (
                <span className="btn-content"><span className="spinner"></span> Simulating...</span>
              ) : "Run Simulation"}
            </button>
          </div>

          <div className="simulator-body">
            {!simulationResult && !simulating && (
              <div className="empty-state">
                Adjust a policy setting on the left (e.g. lower the budget) and click Run Simulation to see the financial impact.
              </div>
            )}
            
            {simulating && (
               <div className="processing-state" style={{ padding: '2rem 1rem' }}>
                  <div className="processing-icon"><span className="spinner large-spinner"></span></div>
                  <h3 style={{fontSize: '1rem'}}>Re-running 10,000 events...</h3>
               </div>
            )}
            
            {simulationResult && (
              <div className="simulation-stats">
                <div className="stat-row">
                  <span>Baseline Recovery:</span>
                  <strong>{formatINR(simulationResult.baseline_revenue_recovered)}</strong>
                </div>
                <div className="stat-row">
                  <span>Hypothetical Recovery:</span>
                  <strong>{formatINR(simulationResult.hypothetical_revenue_recovered)}</strong>
                </div>
                
                <div className="divider"></div>
                
                <div className="stat-row delta">
                  <span>Net Revenue Impact:</span>
                  <strong className={simulationResult.delta >= 0 ? "positive" : "negative"}>
                    {simulationResult.delta > 0 ? "+" : ""}{formatINR(simulationResult.delta)}
                  </strong>
                </div>
                <div className="stat-row mt">
                  <span>Interventions Used:</span>
                  <strong>{simulationResult.intervention_count}</strong>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
