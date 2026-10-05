import JSZip from "jszip";
import type { OpenFile } from './editor-layout';
import type { Assignment } from '@/features/assignments/types';

const EXTENSION_LANGUAGE_MAP: Record<string, string> = {
  py: 'python',
  js: 'javascript',
  jsx: 'javascript',
  ts: 'typescript',
  tsx: 'typescript',
  json: 'json',
  md: 'markdown',
  html: 'html',
  css: 'css',
  scss: 'scss',
  sql: 'sql',
  sh: 'shell',
  bash: 'shell',
  yaml: 'yaml',
  yml: 'yaml',
  xml: 'xml',
  java: 'java',
  c: 'c',
  cpp: 'cpp',
  h: 'c',
  hpp: 'cpp',
  rs: 'rust',
  go: 'go',
  rb: 'ruby',
  php: 'php',
  txt: 'plaintext',
};

const IMAGE_EXTENSIONS = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp']);
const ILLEGAL_FILENAME_CHARS = /[/\\:*?"<>|]/;

export function basename(filename: string) {
  return filename.split(/[/\\]/).pop() ?? filename;
}

export function sanitizeFilename(filename: string): string {
  return filename
    .trim()
    .replace(/^(\.\.[/\\])+/, '')
    .replace(/[/\\]/g, '_');
}

export function validateFilename(
  filename: string,
  existingFiles: string[],
  currentFilename?: string
): { valid: boolean; error?: string } {
  const trimmed = filename.trim();
  if (!trimmed) {
    return { valid: false, error: 'Filename cannot be empty.' };
  }
  if (trimmed.length > 255) {
    return { valid: false, error: 'Filename must be 255 characters or fewer.' };
  }
  if (ILLEGAL_FILENAME_CHARS.test(trimmed)) {
    return { valid: false, error: 'Filename contains invalid characters (/ \\ : * ? " < > |).' };
  }
  if (
    trimmed === '.' ||
    trimmed === '..' ||
    trimmed.startsWith('../') ||
    trimmed.startsWith('..\\')
  ) {
    return { valid: false, error: 'Relative path navigation is not permitted.' };
  }
  const isDuplicate = existingFiles.some(
    (existing) =>
      existing !== currentFilename &&
      existing.toLowerCase() === trimmed.toLowerCase()
  );
  if (isDuplicate) {
    return { valid: false, error: `A file named "${trimmed}" already exists.` };
  }
  return { valid: true };
}

export function checkBundleRequirements(
  files: Record<string, OpenFile>,
  assignment?: Assignment | null
): {
  hasRequiredEntrypoint: boolean;
  expectedEntrypoint: string | null;
  missingRequiredFiles: string[];
} {
  const entrypoint = assignment?.config_json?.bundle?.entrypoint ?? null;
  const workspaceFiles = Object.values(files)
    .filter((f) => f.category === 'workspace')
    .map((f) => f.filename);

  const hasRequiredEntrypoint = !entrypoint || workspaceFiles.includes(entrypoint);

  const missingRequiredFiles: string[] = [];
  const requiredFileConfigs = assignment?.config_json?.bundle?.file_requirements ?? [];
  for (const req of requiredFileConfigs) {
    if (req.paths && req.paths.length > 0) {
      for (const requiredPath of req.paths) {
        if (!workspaceFiles.includes(requiredPath)) {
          missingRequiredFiles.push(requiredPath);
        }
      }
    }
  }

  return {
    hasRequiredEntrypoint,
    expectedEntrypoint: entrypoint,
    missingRequiredFiles,
  };
}

export function languageFromFilename(filename: string) {
  const extension = basename(filename).split('.').pop()?.toLowerCase();
  if (!extension) return 'plaintext';
  if (IMAGE_EXTENSIONS.has(extension)) return 'image';
  return EXTENSION_LANGUAGE_MAP[extension] ?? 'plaintext';
}

export function isImageFilename(filename: string) {
  const extension = basename(filename).split('.').pop()?.toLowerCase();
  return Boolean(extension && IMAGE_EXTENSIONS.has(extension));
}


function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ''));
    reader.onerror = () => reject(reader.error ?? new Error('Failed to read file'));
    reader.readAsDataURL(file);
  });
}

export function dataUrlToBytes(dataUrl: string): Uint8Array<ArrayBuffer> {
  const match = /^data:[^;]+;base64,(.+)$/.exec(dataUrl);
  if (!match) {
    throw new Error('Expected a base64 data URL');
  }
  const binary = atob(match[1]);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

export async function readFilesAsOpenFiles(files: File[]) {
  const openFiles: OpenFile[] = [];

  for (const file of files) {
    const filename = basename(file.name);
    const isImage =
      isImageFilename(filename) ||
      (typeof file.type === 'string' && file.type.startsWith('image/'));

    if (isImage) {
      const content = await readFileAsDataUrl(file);
      openFiles.push({
        filename,
        content,
        language: 'image',
        category: 'workspace',
        kind: 'image',
      });
      continue;
    }

    const content = await file.text();
    openFiles.push({
      filename,
      content,
      language: languageFromFilename(filename),
      category: 'workspace',
      kind: 'text',
    });
  }

  return openFiles;
}

export async function createSubmissionBundle(files: Record<string, OpenFile>) {
  const zip = new JSZip();
  const workspaceFiles = Object.values(files).filter((file) => file.category === "workspace");

  if (workspaceFiles.length === 0) {
    zip.file("main.py", "# No workspace files uploaded yet.\n");
  } else {
    for (const file of workspaceFiles) {
      if (file.kind === 'image' || isImageFilename(file.filename)) {
        zip.file(file.filename, dataUrlToBytes(file.content));
      } else {
        zip.file(file.filename, file.content);
      }
    }
  }

  return zip.generateAsync({ type: "blob" });
}

export function downloadFile(filename: string, content: string, kind: OpenFile['kind'] = 'text') {
  const blob =
    kind === 'image' || content.startsWith('data:')
      ? (() => {
          const bytes = dataUrlToBytes(content);
          const mimeMatch = /^data:([^;]+);base64,/.exec(content);
          return new Blob([bytes], {
            type: mimeMatch?.[1] ?? 'application/octet-stream',
          });
        })()
      : new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export async function downloadZipBundle(files: Record<string, OpenFile>, zipName = "workspace.zip") {
  const blob = await createSubmissionBundle(files);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = zipName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
