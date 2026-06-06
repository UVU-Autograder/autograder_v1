'use client';

import { createContext, useContext, useState, ReactNode } from 'react';
import { getFile } from './api';

type OpenFile = {
  filename: string;
  content: string;
  language: string;
} | null;

type AssignmentFileContextType = {
  openFile: OpenFile;
  openFileByName: (filename: string) => Promise<void>;
};

const AssignmentFileContext = createContext<AssignmentFileContextType | null>(null);

export function AssignmentFileProvider({ children }: { children: ReactNode }) {
  const [openFile, setOpenFile] = useState<OpenFile>(null);

  const openFileByName = async (filename: string) => {
    const response = await getFile(filename);
    const content = await response.text();
    const language = filename.endsWith('.py') ? 'python' : 'plaintext';
    setOpenFile({ filename, content, language });
  };

  return (
    <AssignmentFileContext.Provider value={{ openFile, openFileByName }}>
      {children}
    </AssignmentFileContext.Provider>
  );
}

export function useAssignmentFile() {
  const ctx = useContext(AssignmentFileContext);
  if (!ctx) throw new Error('useAssignmentFile must be used within AssignmentFileProvider');
  return ctx;
}