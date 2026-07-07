import type { UploadJob } from '../../types/upload';
import { LoadingState } from './LoadingState';
import { ProgressBar } from './ProgressBar';
import { StatusBadge } from './StatusBadge';
import { Timeline } from './Timeline';

interface PipelineTrackerProps {
  job: UploadJob | null;
  loading: boolean;
}

export function PipelineTracker({ job, loading }: PipelineTrackerProps) {
  if (loading && !job) {
    return <LoadingState label="Loading pipeline status" />;
  }

  if (!job) {
    return (
      <section className="pipeline-tracker">
        <h2>Pipeline Status</h2>
        <p>Select or upload a file to view the live processing state.</p>
      </section>
    );
  }

  return (
    <section className="pipeline-tracker">
      <div className="pipeline-tracker__header">
        <div>
          <h2>{job.fileName}</h2>
          <p>Current Step: {job.currentStep}</p>
        </div>
        <StatusBadge status={job.status} />
      </div>
      <ProgressBar value={job.progress} />
      <dl className="pipeline-tracker__meta">
        <div><dt>Estimated Time</dt><dd>{job.estimatedTime}</dd></div>
        <div><dt>Progress</dt><dd>{job.progress}%</dd></div>
        <div><dt>Output File</dt><dd>{job.outputFile || 'Pending'}</dd></div>
      </dl>
      <Timeline items={job.timeline} />
      <div className="pipeline-logs">
        <h3>Processing Logs</h3>
        <ul>
          {job.logs.map((log) => <li key={log}>{log}</li>)}
        </ul>
      </div>
    </section>
  );
}
