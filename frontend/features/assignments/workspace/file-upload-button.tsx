'use client';

import { Button } from '@/components/ui/button';
import { UploadIcon } from 'lucide-react';
import { useRef } from 'react';

type FileUploadButtonProps = {
  onFilesSelected: (files: FileList | File[]) => void | Promise<void>;
  multiple?: boolean;
  accept?: string;
  className?: string;
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon" | "xs";
  title?: string;
  children?: React.ReactNode;
};

export function FileUploadButton({
  onFilesSelected,
  multiple = true,
  accept,
  className,
  variant = "outline",
  size = "sm",
  title,
  children,
}: FileUploadButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        multiple={multiple}
        accept={accept}
        className="hidden"
        onChange={(event) => {
          const selected = event.target.files;
          if (!selected || selected.length === 0) return;
          void onFilesSelected(selected);
          event.target.value = '';
        }}
      />
      <Button
        type="button"
        variant={variant}
        size={size}
        className={className}
        title={title}
        onClick={() => inputRef.current?.click()}
      >
        {children ?? (
          <>
            <UploadIcon className="size-3.5" />
            <span>Upload files</span>
          </>
        )}
      </Button>
    </>
  );
}
