interface RetryButtonProps {
  onRetry: () => void;
  disabled?: boolean;
}

export function RetryButton({ onRetry, disabled = false }: RetryButtonProps) {
  return (
    <button className="upload-button upload-button--secondary" type="button" onClick={onRetry} disabled={disabled}>
      Retry
    </button>
  );
}
