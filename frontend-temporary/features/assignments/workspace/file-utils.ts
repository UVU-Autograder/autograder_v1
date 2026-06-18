import type { OpenFile } from './editor-layout';

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

export function basename(filename: string) {
  return filename.split(/[/\\]/).pop() ?? filename;
}

export function languageFromFilename(filename: string) {
  const extension = basename(filename).split('.').pop()?.toLowerCase();
  if (!extension) return 'plaintext';
  return EXTENSION_LANGUAGE_MAP[extension] ?? 'plaintext';
}

export async function readFilesAsOpenFiles(files: File[]) {
  const openFiles: OpenFile[] = [];

  for (const file of files) {
    const filename = basename(file.name);
    const content = await file.text();
    openFiles.push({
      filename,
      content,
      language: languageFromFilename(filename),
      category: 'workspace',
    });
  }

  return openFiles;
}
