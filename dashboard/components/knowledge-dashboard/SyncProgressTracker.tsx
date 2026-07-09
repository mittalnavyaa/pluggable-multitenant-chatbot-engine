// dashboard/components/knowledge-dashboard/SyncProgressTracker.tsx

import React from 'react';
import { PIPELINE_SYNC_STEPS } from '../../hooks/useKnowledgeSync';

interface SyncProgressTrackerProps {
  currentStep: number;
  progress: number;
  duration: number;
  jobId: string | null;
  onCancel: () => void;
}

export const SyncProgressTracker: React.FC<SyncProgressTrackerProps> = ({
  currentStep,
  progress,
  duration,
  jobId,
  onCancel
}) => {
  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = secs % 60;
    return `${mins}:${remainingSecs.toString().padStart(2, '0')}`;
  };

  return (
    <section className="sync-tracker-panel" aria-label="Synchronization Progress Tracker">
      <div className="sync-tracker-panel__header">
        <div>
          <h3 className="sync-tracker-panel__title">Synchronizing Chatbot Brain...</h3>
          {jobId && <span className="sync-tracker-panel__job-id">Job ID: {jobId}</span>}
        </div>
        <div className="sync-tracker-panel__meta">
          <span>Elapsed Time: <strong>{formatTime(duration)}</strong></span>
          <button type="button" className="btn-cancel-sync" onClick={onCancel}>Cancel</button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="sync-progress-bar-container">
        <div 
          className="sync-progress-bar" 
          style={{ width: `${progress}%` }} 
          role="progressbar" 
          aria-valuenow={progress} 
          aria-valuemin={0} 
          aria-valuemax={100}
        />
        <span className="sync-progress-percent">{progress}%</span>
      </div>

      {/* Steps List */}
      <div className="sync-steps-list">
        {PIPELINE_SYNC_STEPS.map((step, idx) => {
          let stepClass = 'pending';
          if (idx < currentStep) {
            stepClass = 'complete';
          } else if (idx === currentStep) {
            stepClass = 'active';
          }

          return (
            <div key={step.id} className={`sync-step-item sync-step-item--${stepClass}`}>
              <div className="sync-step-dot">
                {idx < currentStep ? (
                  <svg width="10" height="10" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M3 8.5l3.5 3.5L13 4" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                ) : (
                  <span>{idx + 1}</span>
                )}
              </div>
              <span className="sync-step-label">{step.label}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
};
export default SyncProgressTracker;
