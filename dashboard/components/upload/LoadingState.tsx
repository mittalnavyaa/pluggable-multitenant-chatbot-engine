interface LoadingStateProps {
  label: string;
}

export function LoadingState({ label }: LoadingStateProps) {
  return (
    <section className="upload-loading" aria-live="polite">
      <span />
      <p>{label}</p>
    </section>
  );
}
