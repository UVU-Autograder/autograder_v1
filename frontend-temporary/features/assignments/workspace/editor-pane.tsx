'use client';

import MonacoEditor from '@/components/monaco-editor';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { XIcon } from 'lucide-react';
import { useState } from 'react';
import { useAssignmentFile } from './assingment-file-context';

type DropZone = 'top' | 'bottom' | null;

function EditorDropOverlay({
  dropZone,
  onDragLeave,
  onDragOverTop,
  onDragOverBottom,
  onDropTop,
  onDropBottom,
}: {
  dropZone: DropZone;
  onDragLeave: (event: React.DragEvent) => void;
  onDragOverTop: (event: React.DragEvent) => void;
  onDragOverBottom: (event: React.DragEvent) => void;
  onDropTop: (event: React.DragEvent) => void;
  onDropBottom: (event: React.DragEvent) => void;
}) {
  return (
    <div className="absolute inset-0 z-10" onDragLeave={onDragLeave}>
      <div
        className={`absolute top-0 left-0 h-1/2 w-full transition-colors ${
          dropZone === 'top' ? 'bg-primary/20' : 'bg-transparent'
        }`}
        onDragOver={onDragOverTop}
        onDrop={onDropTop}
      />
      <div
        className={`absolute bottom-0 left-0 h-1/2 w-full transition-colors ${
          dropZone === 'bottom' ? 'bg-primary/20' : 'bg-transparent'
        }`}
        onDragOver={onDragOverBottom}
        onDrop={onDropBottom}
      />
      {dropZone && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center" />
      )}
    </div>
  );
}

export function EditorPane({ paneId }: { paneId: string }) {
  const {
    files,
    panes,
    activePaneId,
    dragTab,
    setActiveTab,
    setActivePane,
    closeTab,
    startTabDrag,
    endTabDrag,
    splitTabToPane,
    moveTabToPane,
  } = useAssignmentFile();

  const pane = panes[paneId];
  const [dropZone, setDropZone] = useState<DropZone>(null);

  if (!pane) return null;

  const isDragging = dragTab !== null;
  const isActivePane = activePaneId === paneId;
  const activeTab = pane.activeTab;

  const handleDragOver = (event: React.DragEvent, zone: DropZone) => {
    if (!dragTab) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    setDropZone(zone);
  };

  const handleDropTop = (event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setDropZone(null);

    const droppedTab = dragTab;
    if (!droppedTab) return;

    moveTabToPane(droppedTab.filename, droppedTab.sourcePaneId, paneId);
  };

  const handleDropBottom = (event: React.DragEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setDropZone(null);

    const droppedTab = dragTab;
    if (!droppedTab) return;

    splitTabToPane(droppedTab.filename, droppedTab.sourcePaneId, paneId, 'column');
  };

  const dropOverlayProps = {
    dropZone,
    onDragLeave: (event: React.DragEvent) => {
      if (event.currentTarget === event.target) setDropZone(null);
    },
    onDragOverTop: (event: React.DragEvent) => handleDragOver(event, 'top'),
    onDragOverBottom: (event: React.DragEvent) => handleDragOver(event, 'bottom'),
    onDropTop: handleDropTop,
    onDropBottom: handleDropBottom,
  };

  return (
    <div
      className={`flex h-full min-h-0 min-w-0 flex-1 flex-col ${isActivePane ? 'ring-1 ring-inset ring-primary/30' : ''}`}
      onMouseDown={() => setActivePane(paneId)}
    >
      {pane.tabs.length > 0 && activeTab ? (
        <Tabs
          value={activeTab}
          onValueChange={(filename) => setActiveTab(paneId, filename)}
          className="flex min-h-0 flex-1 flex-col gap-0 p-0"
        >
          <TabsList className="w-full shrink-0 justify-start rounded-none p-0">
            {pane.tabs.map((filename) => (
              <div
                key={filename}
                draggable
                onDragStart={(event) => {
                  event.dataTransfer.effectAllowed = 'move';
                  event.dataTransfer.setData('text/plain', filename);
                  startTabDrag({ filename, sourcePaneId: paneId });
                }}
                onDragEnd={endTabDrag}
                className="inline-flex items-stretch border-r border-border last:border-r-0 data-[active=true]:bg-background"
                data-active={activeTab === filename}
                onMouseDown={(event) => {
                  if (event.button === 1) {
                    event.preventDefault();
                    closeTab(paneId, filename);
                  }
                }}
              >
                <TabsTrigger className="max-w-48 flex-none rounded-none px-4 py-2" value={filename}>
                  <span className="truncate">{filename}</span>
                </TabsTrigger>
                <button
                  type="button"
                  aria-label={`Close ${filename}`}
                  className="inline-flex items-center justify-center px-1.5 opacity-60 transition-opacity hover:bg-muted hover:opacity-100"
                  onClick={() => closeTab(paneId, filename)}
                >
                  <XIcon className="size-3.5" />
                </button>
              </div>
            ))}
          </TabsList>

          <div className="relative mt-0 min-h-0 flex-1">
            {pane.tabs.map((filename) => {
              const file = files[filename];
              if (!file) return null;

              return (
                <TabsContent
                  key={filename}
                  value={filename}
                  className="mt-0 h-full min-h-0 data-active:flex data-active:flex-1"
                >
                  <MonacoEditor
                    key={`${paneId}-${filename}`}
                    height="100%"
                    width="100%"
                    defaultLanguage={file.language}
                    defaultValue={file.content}
                  />
                </TabsContent>
              );
            })}

            {isDragging && <EditorDropOverlay {...dropOverlayProps} />}
          </div>
        </Tabs>
      ) : (
        <div className="relative flex min-h-0 flex-1 items-center justify-center text-sm text-muted-foreground">
          Open a file from the sidebar
          {isDragging && <EditorDropOverlay {...dropOverlayProps} />}
        </div>
      )}
    </div>
  );
}
