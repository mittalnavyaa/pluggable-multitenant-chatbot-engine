import React from 'react';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
}

interface ErrorStateProps {
  title: string;
  description: string;
  onRetry: () => void;
  icon?: React.ReactNode;
}

const DefaultEmptyIcon = () => (
  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <path d="M8 12h8" />
  </svg>
);

const DefaultErrorIcon = () => (
  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);

export const EmptyState: React.FC<EmptyStateProps> = ({ title, description, icon }) => {
  return (
    <div className="state-overlay">
      <div className="state-overlay__icon" aria-hidden="true">
        {icon || <DefaultEmptyIcon />}
      </div>
      <h3 className="state-overlay__title">{title}</h3>
      <p className="state-overlay__desc">{description}</p>
    </div>
  );
};

export const ErrorState: React.FC<ErrorStateProps> = ({ title, description, onRetry, icon }) => {
  return (
    <div className="state-overlay">
      <div className="state-overlay__icon" aria-hidden="true" style={{ color: 'var(--badge-danger-text)' }}>
        {icon || <DefaultErrorIcon />}
      </div>
      <h3 className="state-overlay__title" style={{ color: 'var(--badge-danger-text)' }}>{title}</h3>
      <p className="state-overlay__desc">{description}</p>
      <button className="state-overlay__btn" type="button" onClick={onRetry}>
        Retry Connection
      </button>
    </div>
  );
};
