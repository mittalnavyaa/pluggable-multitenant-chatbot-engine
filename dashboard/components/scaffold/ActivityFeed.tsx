import React from 'react';
import { ConversationFeedItem } from '../../mock/dashboardMockData';
import { ListSkeleton } from './SkeletonLoader';
import { EmptyState } from './States';

export interface ActivityFeedProps {
  conversations: ConversationFeedItem[];
  loading?: boolean;
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({
  conversations,
  loading = false
}) => {
  if (loading) {
    return <ListSkeleton />;
  }

  if (conversations.length === 0) {
    return (
      <EmptyState
        title="No Live Conversations"
        description="All chatbot channels are currently idle. No active sessions detected."
      />
    );
  }

  return (
    <div className="activity-feed-scaffold">
      {conversations.map((item) => (
        <div key={item.id} className="activity-feed-scaffold__item">
          {/* Avatar */}
          <div className="activity-avatar" aria-hidden="true">
            {item.avatar}
          </div>

          {/* Body */}
          <div className="activity-body">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
              <span className="activity-title" style={{ fontWeight: 600 }}>{item.title}</span>
              <span style={{ fontSize: '0.6875rem', color: 'var(--color-text-faint)' }}>{item.timestamp}</span>
            </div>
            
            <div className="activity-meta">
              <span
                style={{
                  fontSize: '0.6875rem',
                  background: 'var(--color-primary-bg)',
                  color: 'var(--color-primary)',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontWeight: 600
                }}
              >
                {item.intentBadge}
              </span>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '0.6875rem',
                  fontWeight: 600,
                  color:
                    item.status === 'active' ? 'var(--badge-success-text)' :
                    item.status === 'resolved' ? 'var(--color-text-faint)' :
                    'var(--badge-danger-text)'
                }}
              >
                <span
                  style={{
                    width: '5px',
                    height: '5px',
                    borderRadius: '50%',
                    background:
                      item.status === 'active' ? 'var(--badge-success-text)' :
                      item.status === 'resolved' ? 'var(--color-text-faint)' :
                      'var(--badge-danger-text)'
                  }}
                />
                {item.status}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
