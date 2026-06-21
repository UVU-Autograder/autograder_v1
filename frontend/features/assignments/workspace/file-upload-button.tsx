'use client';

import { Button } from '@/components/ui/button';
import { UploadIcon } from 'lucide-react';
import { useRef } from 'react';

type FileUploadButtonProps = {
  onFilesSelected: (files: FileList | File[]) => void | Promise<void>;
  multiple?: boolean;
  accept?: string;
  className?: string;
};

export function FileUploadButton({
  onFilesSelected,
  multiple = true,
  accept,
  className,
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
        variant="outline"
        size="sm"
        className={className}
        onClick={() => inputRef.current?.click()}
      >
        <UploadIcon />
        Upload files
      </Button>
    </>
  );
}
