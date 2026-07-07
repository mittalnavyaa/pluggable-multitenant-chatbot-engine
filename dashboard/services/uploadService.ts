import type { UploadFile, UploadResponse, UploadValidationConfig } from '../types/upload';

export const uploadValidationConfig: UploadValidationConfig = {
  maxFileSizeBytes: 25 * 1024 * 1024,
  supportedExtensions: ['pdf', 'docx', 'txt']
};

const API_BASE_URL = (import.meta.env.VITE_UPLOAD_API_BASE_URL as string | undefined) || 'http://localhost:8000/uploads';

if (import.meta.env.DEV) {
  console.log('[uploadService] API_BASE_URL =', API_BASE_URL);
}

export function validateUploadFile(file: File, existingFiles: UploadFile[]): string[] {
  const errors: string[] = [];
  const extension = file.name.split('.').pop()?.toLowerCase() || '';
  const duplicate = existingFiles.some(
    (item) => item.fileName.toLowerCase() === file.name.toLowerCase() && item.size === file.size
  );

  if (!uploadValidationConfig.supportedExtensions.includes(extension)) {
    errors.push('Unsupported file type. Accepted formats are PDF, DOCX, and TXT.');
  }
  if (file.size > uploadValidationConfig.maxFileSizeBytes) {
    errors.push('File exceeds the 25 MB maximum upload size.');
  }
  if (file.size === 0) {
    errors.push('Empty files cannot be uploaded.');
  }
  if (duplicate) {
    errors.push('Duplicate file already selected.');
  }

  return errors;
}

export function toUploadFile(file: File, existingFiles: UploadFile[]): UploadFile {
  const extension = file.name.split('.').pop()?.toLowerCase() || '';
  const validationErrors = validateUploadFile(file, existingFiles);

  return {
    id: `${file.name}-${file.size}-${file.lastModified}`,
    file,
    fileName: file.name,
    extension,
    size: file.size,
    uploadTime: new Date().toISOString(),
    status: validationErrors.length > 0 ? 'invalid' : 'selected',
    validationErrors
  };
}

export async function uploadFile(uploadFile: UploadFile): Promise<UploadResponse> {
  if (uploadFile.validationErrors.length > 0) {
    throw new Error(uploadFile.validationErrors.join(' '));
  }

  const formData = new FormData();
  formData.append('file', uploadFile.file);

  console.log('[uploadService] POST', API_BASE_URL, 'file:', uploadFile.fileName);

  const response = await fetch(API_BASE_URL, {
    method: 'POST',
    body: formData
  });

  console.log('[uploadService] POST response status:', response.status);

  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(`Upload failed with HTTP ${response.status}: ${text}`);
  }

  const data = await response.json() as UploadResponse;
  console.log('[uploadService] Upload response:', data);
  return data;
}
