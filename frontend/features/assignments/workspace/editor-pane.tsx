import MonacoEditor from '@/components/monaco-editor';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { XIcon } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useAssignmentFile } from './assignment-file-context';
import ProblemOverview from './problem-overview';
import { getConceptsMetadata } from '@/features/assignments/api';
import { ConceptMetadata } from '@/features/assignments/types';

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
    assignment,
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
    uploadFiles,
    updateFileContent,
  } = useAssignmentFile();

  const pane = panes[paneId];
  const [dropZone, setDropZone] = useState<DropZone>(null);
  const [isFileDropActive, setIsFileDropActive] = useState(false);
  const [conceptMeta, setConceptMeta] = useState<Record<string, ConceptMetadata>>({});

  useEffect(() => {
    getConceptsMetadata().then(setConceptMeta).catch(console.error);
  }, []);

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

  const handleExternalDragOver = (event: React.DragEvent) => {
    if (dragTab || !event.dataTransfer.types.includes('Files')) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
    setIsFileDropActive(true);
  };

  const handleExternalDragLeave = (event: React.DragEvent) => {
    if (event.currentTarget === event.target) setIsFileDropActive(false);
  };

  const handleExternalDrop = (event: React.DragEvent) => {
    if (dragTab || !event.dataTransfer.files.length) return;
    event.preventDefault();
    setIsFileDropActive(false);
    void uploadFiles(event.dataTransfer.files);
  };

  return (
    <div
      className={`relative flex h-full min-h-0 min-w-0 flex-1 flex-col ${isActivePane ? 'ring-1 ring-inset ring-primary/30' : ''}`}
      onMouseDown={() => setActivePane(paneId)}
      onDragOver={handleExternalDragOver}
      onDragLeave={handleExternalDragLeave}
      onDrop={handleExternalDrop}
    >
      {pane.tabs.length > 0 && activeTab ? (
        <Tabs
          value={activeTab}
          onValueChange={(filename) => setActiveTab(paneId, filename)}
          className="flex min-h-0 flex-1 flex-col gap-0 p-0"
        >
          <TabsList className="w-full h-9 shrink-0 justify-start rounded-none p-0 overflow-x-auto overflow-y-hidden min-w-0 flex-nowrap border-b border-border bg-muted/80">
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
                className="inline-flex items-center h-full border-r border-border last:border-r-0 data-[active=true]:bg-background text-foreground"
                data-active={activeTab === filename}
                onMouseDown={(event) => {
                  if (event.button === 1) {
                    event.preventDefault();
                    closeTab(paneId, filename);
                  }
                }}
              >
                <TabsTrigger className="max-w-48 flex-none rounded-none px-3 py-1 text-xs h-full" value={filename}>
                  <span className="truncate">{filename}</span>
                </TabsTrigger>
                <button
                  type="button"
                  aria-label={`Close ${filename}`}
                  className="inline-flex items-center justify-center px-1.5 h-full opacity-60 transition-opacity hover:bg-muted hover:opacity-100 cursor-pointer"
                  onClick={() => closeTab(paneId, filename)}
                >
                  <XIcon className="size-3.5" />
                </button>
              </div>
            ))}
          </TabsList>

          <div className="relative mt-0 min-h-0 min-w-0 w-full flex-1 overflow-hidden">
            {pane.tabs.map((filename) => {
              const file = files[filename];
              if (!file) return null;

              return (
                <TabsContent
                  key={filename}
                  value={filename}
                  className="mt-0 h-full min-h-0 min-w-0 w-full overflow-hidden data-active:flex data-active:flex-1 data-active:flex-col"
                >
                  {file.category === 'overview' || filename === 'Problem Overview' ? (
                    assignment ? (
                      <ProblemOverview assignment={assignment} conceptMeta={conceptMeta} />
                    ) : (
                      <div className="p-4 text-sm text-slate-500">{file.content}</div>
                    )
                  ) : (
                    <MonacoEditor
                      key={`${paneId}-${filename}`}
                      height="100%"
                      width="100%"
                      defaultLanguage={file.language}
                      defaultValue={file.content}
                      onChange={(val) => updateFileContent(filename, val ?? '')}
                      options={{ readOnly: file.category !== 'workspace' }}
                    />
                  )}
                </TabsContent>
              );
            })}

            {isDragging && <EditorDropOverlay {...dropOverlayProps} />}
          </div>
        </Tabs>
      ) : (
        <div className="relative flex min-h-0 flex-1 flex-col items-center justify-center gap-2 text-sm text-muted-foreground">
          <span>Open a file from the sidebar or drop files here</span>
          {isDragging && <EditorDropOverlay {...dropOverlayProps} />}
        </div>
      )}
      {isFileDropActive && (
        <div className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center border-2 border-dashed border-primary bg-primary/10">
          <span className="rounded-md bg-background px-3 py-1.5 text-sm font-medium text-foreground shadow-sm">
            Drop files to open in editor
          </span>
        </div>
      )}
    </div>
  );
}
