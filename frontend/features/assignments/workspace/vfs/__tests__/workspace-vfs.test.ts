import { describe, expect, it } from 'vitest';
import { WorkspaceVFS } from '../workspace-vfs';

describe('WorkspaceVFS - Virtual File System', () => {
  it('initializes with starter files and tracks starter templates', () => {
    const vfs = new WorkspaceVFS({
      'main.py': {
        filename: 'main.py',
        content: 'def solve(): pass',
        language: 'python',
        category: 'workspace',
      },
      'README.md': {
        filename: 'README.md',
        content: '# Instructions',
        language: 'markdown',
        category: 'overview',
      },
    });

    expect(vfs.hasFile('main.py')).toBe(true);
    expect(vfs.hasFile('README.md')).toBe(true);
    expect(vfs.hasFile('missing.py')).toBe(false);

    expect(vfs.readFile('main.py')?.content).toBe('def solve(): pass');
    expect(vfs.readFile('main.py')?.isStarter).toBe(true);
    expect(vfs.isDirty()).toBe(false);
  });

  it('writes new files and updates existing file content', () => {
    const vfs = new WorkspaceVFS();

    const created = vfs.writeFile('solution.py', 'print("hello world")');
    expect(created.filename).toBe('solution.py');
    expect(created.language).toBe('python');
    expect(created.category).toBe('workspace');
    expect(vfs.readFile('solution.py')?.content).toBe('print("hello world")');

    // Update existing
    vfs.writeFile('solution.py', 'print("updated")');
    expect(vfs.readFile('solution.py')?.content).toBe('print("updated")');
  });

  it('rejects invalid or duplicate filenames when writing new files', () => {
    const vfs = new WorkspaceVFS();
    vfs.writeFile('file1.py', 'x = 1');

    expect(() => vfs.writeFile('file1.py/invalid', 'bad')).toThrow();
    expect(() => vfs.writeFile('../evil.py', 'bad')).toThrow();
    expect(() => vfs.writeFile('  ', 'bad')).toThrow();
  });

  it('deletes files properly', () => {
    const vfs = new WorkspaceVFS();
    vfs.writeFile('temp.py', 'x = 1');
    expect(vfs.hasFile('temp.py')).toBe(true);

    const deleted = vfs.deleteFile('temp.py');
    expect(deleted).toBe(true);
    expect(vfs.hasFile('temp.py')).toBe(false);

    const deleteMissing = vfs.deleteFile('temp.py');
    expect(deleteMissing).toBe(false);
  });

  it('renames files and updates language detection', () => {
    const vfs = new WorkspaceVFS();
    vfs.writeFile('notes.txt', 'hello', { category: 'workspace' });

    expect(vfs.readFile('notes.txt')?.language).toBe('plaintext');

    const success = vfs.renameFile('notes.txt', 'notes.py');
    expect(success).toBe(true);
    expect(vfs.hasFile('notes.txt')).toBe(false);
    expect(vfs.hasFile('notes.py')).toBe(true);
    expect(vfs.readFile('notes.py')?.language).toBe('python');
  });

  it('rejects renaming non-workspace or duplicate files', () => {
    const vfs = new WorkspaceVFS();
    vfs.writeFile('overview.md', 'docs', { category: 'overview' });
    vfs.writeFile('test.py', 'assert True', { category: 'workspace' });

    // Cannot rename non-workspace file
    expect(vfs.renameFile('overview.md', 'new_overview.md')).toBe(false);

    // Cannot rename to existing file
    expect(vfs.renameFile('test.py', 'overview.md')).toBe(false);
  });

  it('accurately tracks dirty state against starter templates', () => {
    const vfs = new WorkspaceVFS({
      'main.py': {
        filename: 'main.py',
        content: 'starter',
        language: 'python',
        category: 'workspace',
      },
    });

    expect(vfs.isDirty()).toBe(false);
    expect(vfs.isDirty('main.py')).toBe(false);

    // Modify file
    vfs.writeFile('main.py', 'modified');
    expect(vfs.isDirty()).toBe(true);
    expect(vfs.isDirty('main.py')).toBe(true);

    // Add new file
    vfs.writeFile('helper.py', 'def h(): pass');
    expect(vfs.isDirty('helper.py')).toBe(true);

    // Reset single file
    vfs.resetToTemplate('main.py');
    expect(vfs.readFile('main.py')?.content).toBe('starter');
    expect(vfs.isDirty('main.py')).toBe(false);
    expect(vfs.isDirty()).toBe(true); // helper.py still exists

    // Reset all
    vfs.resetToTemplate();
    expect(vfs.hasFile('helper.py')).toBe(false);
    expect(vfs.isDirty()).toBe(false);
  });

  it('compiles workspace files to a JSZip blob and extracts round-trip', async () => {
    const vfs = new WorkspaceVFS();
    vfs.writeFile('main.py', 'print("hello")', { category: 'workspace' });
    vfs.writeFile('helper.py', 'VALUE = 42', { category: 'workspace' });
    vfs.writeFile('guide.md', '# Guide', { category: 'overview' }); // Should be excluded from zip

    const zipBlob = await vfs.toZipBlob();
    expect(zipBlob).toBeInstanceOf(Blob);
    expect(zipBlob.size).toBeGreaterThan(0);

    // Round-trip into a new VFS
    const roundTripVFS = new WorkspaceVFS();
    const imported = await roundTripVFS.fromZipBlob(zipBlob);

    expect(imported).toContain('main.py');
    expect(imported).toContain('helper.py');
    expect(imported).not.toContain('guide.md');

    expect(roundTripVFS.readFile('main.py')?.content).toBe('print("hello")');
    expect(roundTripVFS.readFile('helper.py')?.content).toBe('VALUE = 42');
  });

  it('generates a submission payload with files record and zip blob', async () => {
    const vfs = new WorkspaceVFS();
    vfs.writeFile('code.py', 'x = 10', { category: 'workspace' });

    const payload = await vfs.toSubmissionPayload();
    expect(payload.files).toEqual({ 'code.py': 'x = 10' });
    expect(payload.zipBlob).toBeInstanceOf(Blob);
  });
});
