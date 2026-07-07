interface UploadButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

export function UploadButton({ label, onClick, disabled = false }: UploadButtonProps) {
  return (
    <button className="upload-button" type="button" onClick={onClick} disabled={disabled}>
      {label}
    </button>
  );
}
