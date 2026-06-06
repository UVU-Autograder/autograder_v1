'use client';

import { createContext, useContext, useState, ReactNode } from 'react';
import { getFile } from './api';

type OpenFile = {
  filename: string;
  content: string;
  language: string;
};

type AssignmentFileContextType = {
  openFiles: OpenFile[];
  activeFile: string | null;
  openFileByName: (filename: string) => Promise<void>;
  setActiveFile: (filename: string) => void;
  closeFile: (filename: string) => void;
};

const AssignmentFileContext = createContext<AssignmentFileContextType | null>(null);

export function AssignmentFileProvider({ children }: { children: ReactNode }) {
  const [openFiles, setOpenFiles] = useState<OpenFile[]>([]);
  const [activeFile, setActiveFile] = useState<string | null>(null);

  const openFileByName = async (filename: string) => {
    let alreadyOpen = false;
    setOpenFiles((prev) => {
      alreadyOpen = prev.some((file) => file.filename === filename);
      if (alreadyOpen) {
        setActiveFile(filename);
      }
      return prev;
    });
    if (alreadyOpen) return;

    const response = await getFile(filename);
    const content = await response.text();
    const language = filename.endsWith('.py') ? 'python' : 'plaintext';
    const file = { filename, content, language };

    setOpenFiles((prev) => [...prev, file]);
    setActiveFile(filename);
  };

  const closeFile = (filename: string) => {
    setOpenFiles((prev) => {
      const closingIndex = prev.findIndex((file) => file.filename === filename);
      if (closingIndex === -1) return prev;

      const nextFiles = prev.filter((file) => file.filename !== filename);

      setActiveFile((currentActive) => {
        if (currentActive !== filename) return currentActive;
        if (nextFiles.length === 0) return null;
        return nextFiles[Math.min(closingIndex, nextFiles.length - 1)].filename;
      });

      return nextFiles;
    });
  };

  return (
    <AssignmentFileContext.Provider value={{ openFiles, activeFile, openFileByName, setActiveFile, closeFile }}>
      {children}
    </AssignmentFileContext.Provider>
  );
}

export function useAssignmentFile() {
  const ctx = useContext(AssignmentFileContext);
  if (!ctx) throw new Error('useAssignmentFile must be used within AssignmentFileProvider');
  return ctx;
}