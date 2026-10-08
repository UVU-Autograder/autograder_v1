import JSZip from 'jszip';
import type { FileCategory, OpenFile } from '../editor-layout';
import {
  dataUrlToBytes,
  isImageFilename,
  languageFromFilename,
  validateFilename,
  sanitizeFilename,
} from '../file-utils';

export interface VFSFile extends OpenFile {
  isStarter?: boolean;
  originalContent?: string;
}

export type WriteFileOptions = {
  category?: FileCategory;
  language?: string;
  kind?: 'text' | 'image';
  isStarter?: boolean;
};

/**
 * Pure, framework-agnostic Virtual File System for managing assignment code files,
 * buffer state mutations, dirty tracking against starter templates, and ZIP compilation.
 */
export class WorkspaceVFS {
  private files: Map<string, VFSFile> = new Map();
  private starterSnapshots: Map<string, VFSFile> = new Map();

  constructor(initialFiles?: Record<string, OpenFile> | VFSFile[]) {
    if (initialFiles) {
      this.initStarterTemplate(initialFiles);
    }
  }

  /**
   * Initializes or replaces the starter template snapshot and current files.
   */
  public initStarterTemplate(initialFiles: Record<string, OpenFile> | VFSFile[]): void {
    this.files.clear();
    this.starterSnapshots.clear();

    const fileList: OpenFile[] = Array.isArray(initialFiles)
      ? initialFiles
      : Object.values(initialFiles);

    for (const file of fileList) {
      const vfsFile: VFSFile = {
        ...file,
        isStarter: true,
        originalContent: file.content,
      };
      this.files.set(file.filename, { ...vfsFile });
      this.starterSnapshots.set(file.filename, { ...vfsFile });
    }
  }

  /**
   * Retrieves a file by name.
   */
  public readFile(filename: string): VFSFile | undefined {
    return this.files.get(filename);
  }

  /**
   * Checks whether a file exists.
   */
  public hasFile(filename: string): boolean {
    return this.files.has(filename);
  }

  /**
   * Lists all files, optionally filtered by category.
   */
  public listFiles(category?: FileCategory): VFSFile[] {
    const all = Array.from(this.files.values());
    if (!category) return all;
    return all.filter((f) => f.category === category);
  }

  /**
   * Returns a snapshot of all files as a plain Record dictionary.
   */
  public getAllFilesRecord(): Record<string, VFSFile> {
    const record: Record<string, VFSFile> = {};
    for (const [name, file] of this.files.entries()) {
      record[name] = { ...file };
    }
    return record;
  }

  /**
   * Lists filenames, optionally filtered by category.
   */
  public listFilenames(category?: FileCategory): string[] {
    return this.listFiles(category).map((f) => f.filename);
  }

  /**
   * Writes content to an existing or new file in the VFS.
   */
  public writeFile(
    filename: string,
    content: string,
    options?: WriteFileOptions
  ): VFSFile {
    const trimmed = filename.trim();
    const existing = this.files.get(trimmed);

    if (existing) {
      existing.content = content;
      if (options?.language) existing.language = options.language;
      if (options?.category) existing.category = options.category;
      if (options?.kind) existing.kind = options.kind;
      if (options?.isStarter) {
        existing.isStarter = true;
        existing.originalContent = content;
        this.starterSnapshots.set(trimmed, { ...existing });
      }
      return existing;
    }

    // New file validation
    const validation = validateFilename(trimmed, this.listFilenames());
    if (!validation.valid) {
      throw new Error(validation.error ?? `Invalid filename: ${trimmed}`);
    }

    const isImage = options?.kind === 'image' || isImageFilename(trimmed);
    const newFile: VFSFile = {
      filename: trimmed,
      content,
      language: options?.language ?? (isImage ? 'image' : languageFromFilename(trimmed)),
      category: options?.category ?? 'workspace',
      kind: options?.kind ?? (isImage ? 'image' : 'text'),
      isStarter: options?.isStarter ?? false,
      originalContent: options?.isStarter ? content : undefined,
    };

    this.files.set(trimmed, newFile);
    if (options?.isStarter) {
      this.starterSnapshots.set(trimmed, { ...newFile });
    }
    return newFile;
  }

  /**
   * Deletes a file from the VFS. Returns true if removed, false if not found.
   */
  public deleteFile(filename: string): boolean {
    return this.files.delete(filename.trim());
  }

  /**
   * Renames a workspace file. Returns true on success, false if rejected.
   */
  public renameFile(oldFilename: string, newFilename: string): boolean {
    const trimmedOld = oldFilename.trim();
    const trimmedNew = newFilename.trim();

    if (!trimmedOld || !trimmedNew || trimmedOld === trimmedNew) {
      return false;
    }

    const existing = this.files.get(trimmedOld);
    if (!existing || existing.category !== 'workspace') {
      return false;
    }

    const validation = validateFilename(trimmedNew, this.listFilenames(), trimmedOld);
    if (!validation.valid) {
      return false;
    }

    this.files.delete(trimmedOld);
    const renamedFile: VFSFile = {
      ...existing,
      filename: trimmedNew,
      language: existing.kind === 'image' ? 'image' : languageFromFilename(trimmedNew),
    };
    this.files.set(trimmedNew, renamedFile);
    return true;
  }

  /**
   * Determines if a specific file or the overall VFS has been modified relative to the starter template.
   */
  public isDirty(filename?: string): boolean {
    if (filename) {
      const current = this.files.get(filename.trim());
      if (!current) {
        return this.starterSnapshots.has(filename.trim());
      }
      const starter = this.starterSnapshots.get(filename.trim());
      if (!starter) return true; // Newly created file
      return current.content !== starter.content;
    }

    // Check all files
    if (this.files.size !== this.starterSnapshots.size) return true;

    for (const [name, starter] of this.starterSnapshots.entries()) {
      const current = this.files.get(name);
      if (!current || current.content !== starter.content) {
        return true;
      }
    }

    for (const name of this.files.keys()) {
      if (!this.starterSnapshots.has(name)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Resets a specific file or the entire VFS to the starter template snapshot.
   */
  public resetToTemplate(filename?: string): void {
    if (filename) {
      const trimmed = filename.trim();
      const starter = this.starterSnapshots.get(trimmed);
      if (starter) {
        this.files.set(trimmed, { ...starter });
      } else {
        this.files.delete(trimmed);
      }
      return;
    }

    this.files.clear();
    for (const [name, starter] of this.starterSnapshots.entries()) {
      this.files.set(name, { ...starter });
    }
  }

  /**
   * Packages workspace category files into a JSZip Blob.
   */
  public async toZipBlob(): Promise<Blob> {
    const zip = new JSZip();
    const workspaceFiles = this.listFiles('workspace');

    if (workspaceFiles.length === 0) {
      zip.file('main.py', '# No workspace files uploaded yet.\n');
    } else {
      for (const file of workspaceFiles) {
        if (file.kind === 'image' || isImageFilename(file.filename)) {
          zip.file(file.filename, dataUrlToBytes(file.content));
        } else {
          zip.file(file.filename, file.content);
        }
      }
    }

    return zip.generateAsync({ type: 'blob' });
  }

  /**
   * Imports files from a ZIP archive Blob into the workspace category.
   * Returns an array of imported filenames.
   */
  public async fromZipBlob(blob: Blob): Promise<string[]> {
    const zip = await JSZip.loadAsync(blob);
    const importedFilenames: string[] = [];

    for (const [rawPath, zipEntry] of Object.entries(zip.files)) {
      if (zipEntry.dir) continue;

      const cleanName = sanitizeFilename(rawPath);
      if (!cleanName) continue;

      const isImage = isImageFilename(cleanName);
      let content = '';

      if (isImage) {
        const base64 = await zipEntry.async('base64');
        const ext = cleanName.split('.').pop()?.toLowerCase() ?? 'png';
        const mime = ext === 'jpg' ? 'jpeg' : ext;
        content = `data:image/${mime};base64,${base64}`;
      } else {
        content = await zipEntry.async('text');
      }

      this.writeFile(cleanName, content, {
        category: 'workspace',
        kind: isImage ? 'image' : 'text',
      });
      importedFilenames.push(cleanName);
    }

    return importedFilenames;
  }

  /**
   * Compiles workspace files into a submission payload structure.
   */
  public async toSubmissionPayload(): Promise<{
    files: Record<string, string>;
    zipBlob: Blob;
  }> {
    const fileMap: Record<string, string> = {};
    for (const file of this.listFiles('workspace')) {
      fileMap[file.filename] = file.content;
    }
    const zipBlob = await this.toZipBlob();
    return { files: fileMap, zipBlob };
  }
}
