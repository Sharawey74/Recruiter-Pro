"use client";

import { useCallback, useRef, useState, type DragEvent } from "react";
import { UploadCloud, FolderOpen, CheckCircle2, FileText, X } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * One definition of what this application accepts, used by every upload
 * surface.
 *
 * The dashboard's drop handler took `file.type === "application/pdf"` and
 * dropped everything else on the floor without saying so, while its own file
 * picker advertised `.pdf,.docx` and the Upload page accepted PDF, DOCX and
 * TXT. Dragging a .docx onto the dashboard therefore did nothing at all — no
 * file selected, no message. The backend has always accepted all three.
 */
export const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".txt"] as const;
export const ACCEPT_ATTRIBUTE = ACCEPTED_EXTENSIONS.join(",");
/** Matches the API's own ceiling; rejecting here saves a doomed round trip. */
export const MAX_FILE_BYTES = 10 * 1024 * 1024;

export function describeRejection(file: File): string | null {
  const name = file.name.toLowerCase();
  const extension = name.slice(name.lastIndexOf("."));

  if (!ACCEPTED_EXTENSIONS.includes(extension as (typeof ACCEPTED_EXTENSIONS)[number])) {
    return `${file.name} is not a supported format. Use PDF, DOCX or TXT.`;
  }
  if (file.size > MAX_FILE_BYTES) {
    return `${file.name} is ${(file.size / 1024 / 1024).toFixed(1)} MB. The limit is 10 MB.`;
  }
  if (file.size === 0) {
    return `${file.name} is empty.`;
  }
  return null;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

interface CvDropzoneProps {
  files: File[];
  onFilesAdded: (files: File[]) => void;
  onRemove: (index: number) => void;
  /** Reported for each file that fails validation, so nothing is silently dropped. */
  onReject: (message: string) => void;
  multiple?: boolean;
  disabled?: boolean;
}

export function CvDropzone({
  files,
  onFilesAdded,
  onRemove,
  onReject,
  multiple = false,
  disabled = false,
}: CvDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const accept = useCallback(
    (incoming: FileList | null) => {
      if (!incoming || incoming.length === 0) return;

      const accepted: File[] = [];
      for (const file of Array.from(incoming)) {
        const rejection = describeRejection(file);
        if (rejection) onReject(rejection);
        else accepted.push(file);
      }

      if (accepted.length > 0) {
        onFilesAdded(multiple ? accepted : accepted.slice(0, 1));
      }
    },
    [multiple, onFilesAdded, onReject]
  );

  const onDrag = (event: DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    if (disabled) return;
    setIsDragging(event.type === "dragenter" || event.type === "dragover");
  };

  const onDrop = (event: DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
    if (!disabled) accept(event.dataTransfer.files);
  };

  return (
    <div className="flex h-full flex-col gap-4">
      <div
        onDragEnter={onDrag}
        onDragOver={onDrag}
        onDragLeave={onDrag}
        onDrop={onDrop}
        className={cn(
          "group flex flex-1 flex-col items-center justify-center rounded-lg border border-dashed p-8 text-center transition-all duration-300",
          "min-h-[340px] bg-surface-container-low/40 backdrop-blur-xl",
          isDragging
            ? "border-primary bg-primary/10"
            : "border-primary/20 hover:border-primary/50",
          disabled && "pointer-events-none opacity-60"
        )}
      >
        <div
          className={cn(
            "mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-primary/10 transition-transform duration-500",
            isDragging ? "scale-110 bg-primary/20" : "group-hover:scale-105"
          )}
        >
          <UploadCloud className="h-9 w-9 text-primary" aria-hidden />
        </div>

        <h3 className="mb-2 text-headline-md text-on-surface">
          {isDragging ? "Drop to upload" : "Drag & drop resumes"}
        </h3>
        <p className="mb-8 max-w-md text-on-surface-variant">
          Upload {multiple ? "one or more documents" : "a document"} to analyse against
          the current job database.
        </p>

        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT_ATTRIBUTE}
          multiple={multiple}
          disabled={disabled}
          onChange={(event) => {
            accept(event.target.files);
            // Reset, or selecting the same file twice in a row fires no change
            // event and the second attempt appears to do nothing.
            event.target.value = "";
          }}
          className="sr-only"
          id="cv-file-input"
        />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={disabled}
          className="btn-secondary"
        >
          <FolderOpen className="h-5 w-5" aria-hidden />
          Browse files
        </button>

        <div className="label-sm mt-8 flex flex-wrap items-center justify-center gap-4 text-on-surface-variant/70">
          {ACCEPTED_EXTENSIONS.map((extension) => (
            <span key={extension} className="flex items-center gap-1">
              <CheckCircle2 className="h-4 w-4" aria-hidden />
              {extension.slice(1)}
            </span>
          ))}
          <span className="border-l border-white/10 pl-4">Max 10 MB</span>
        </div>
      </div>

      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map((file, index) => (
            <li
              key={`${file.name}-${file.lastModified}-${index}`}
              className="flex items-center justify-between gap-3 rounded border border-white/5 bg-surface-container/60 p-4"
            >
              <div className="flex min-w-0 items-center gap-3">
                <FileText className="h-5 w-5 shrink-0 text-primary" aria-hidden />
                <div className="min-w-0">
                  <p className="truncate font-medium text-on-surface">{file.name}</p>
                  <p className="label-sm text-tertiary">{formatFileSize(file.size)}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => onRemove(index)}
                aria-label={`Remove ${file.name}`}
                className="shrink-0 rounded p-1 text-tertiary transition-colors hover:text-error"
              >
                <X className="h-5 w-5" aria-hidden />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
