// dashboard/components/knowledge-dashboard/ActivityFeed.tsx

import React from 'react';

interface ActivityItem {
  id: string;
  type: 'ready' | 'failed' | 'active';
  text: string;
  time: string;
  docName: string;
  product: string;
}

interface ActivityFeedProps {
  feed: ActivityItem[];
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ feed }) => {
  return (
    <section className="activity-card" aria-label="Recent Ingestion Activity Feed">
      <h3 className="activity-card__title">Recent Ingestion Activity</h3>
      
      <div className="activity-list">
        {feed.length === 0 ? (
          <div className="products-empty" style={{ padding: '24px 0' }}>
            <p>No recent activity available.</p>
          </div>
        ) : (
          feed.map((item) => (
            <div
              key={item.id}
              className={`activity-item activity-item--${item.type}`}
            >
              <div className="activity-item__content">
                <span className="activity-item__text">
                  <strong>{item.docName}</strong>: {item.text}
                </span>
                <div className="activity-item__meta">
                  <span>{item.product}</span>
                  <span>{item.time}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
};
