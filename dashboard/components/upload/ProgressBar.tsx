interface ProgressBarProps {
  value: number;
}

export function ProgressBar({ value }: ProgressBarProps) {
  const normalized = Math.max(0, Math.min(100, value));

  return (
    <div className="upload-progress" aria-label="Pipeline progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={normalized} role="progressbar">
      <span style={{ width: `${normalized}%` }} />
    </div>
  );
}
