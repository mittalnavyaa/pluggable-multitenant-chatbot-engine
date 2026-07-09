// dashboard/components/knowledge-dashboard/PipelineTimeline.tsx

import React from 'react';

interface PipelineTimelineProps {
  status: string;
}

const TIMELINE_STEPS = [
  { id: 'uploaded', label: 'Uploaded' },
  { id: 'extracted', label: 'Extracted' },
  { id: 'sanitized', label: 'Sanitized' },
  { id: 'validated', label: 'Validated' },
  { id: 'chunked', label: 'Chunked' },
  { id: 'embedded', label: 'Embedded' },
  { id: 'vectorized', label: 'Vectorized' }
];

export const PipelineTimeline: React.FC<PipelineTimelineProps> = ({ status }) => {
  const normStatus = status.toLowerCase();

  // Find active step index based on current status mapping
  let activeIndex = 0;
  let isFailed = false;

  if (normStatus === 'queued' || normStatus === 'pending') {
    activeIndex = 0;
  } else if (normStatus === 'downloading' || normStatus === 'uploading') {
    activeIndex = 0;
  } else if (normStatus === 'extracting' || normStatus === 'extracting_text') {
    activeIndex = 1;
  } else if (normStatus === 'cleaning' || normStatus === 'ai_formatting') {
    activeIndex = 2;
  } else if (normStatus === 'validating') {
    activeIndex = 3;
  } else if (normStatus === 'validation_failed') {
    activeIndex = 3;
    isFailed = true;
  } else if (normStatus === 'chunking' || normStatus === 'ready_for_chunking' || normStatus === 'generating_markdown') {
    activeIndex = 4;
  } else if (normStatus === 'embedding' || normStatus === 'storing') {
    activeIndex = 5;
  } else if (normStatus === 'ready' || normStatus === 'completed') {
    activeIndex = 6;
  } else if (normStatus === 'failed') {
    activeIndex = 5;
    isFailed = true;
  }

  return (
    <div className="pipeline-timeline" aria-label={`Pipeline Ingestion Progress: ${status}`}>
      {TIMELINE_STEPS.map((step, idx) => {
        let stateClass = 'pending';
        if (isFailed && idx === activeIndex) {
          stateClass = 'failed';
        } else if (idx < activeIndex) {
          stateClass = 'complete';
        } else if (idx === activeIndex) {
          stateClass = normStatus === 'ready' || normStatus === 'completed' ? 'complete' : 'active';
        }

        return (
          <React.Fragment key={step.id}>
            <span className="pipeline-step">
              <span className={`pipeline-dot pipeline-dot--${stateClass}`} />
              <span>{step.label}</span>
            </span>
            {idx < TIMELINE_STEPS.length - 1 && (
              <span className="pipeline-arrow" aria-hidden="true">➔</span>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};
