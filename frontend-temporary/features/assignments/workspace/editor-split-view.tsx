'use client';

import { LayoutNode } from './editor-layout';
import { EditorPane } from './editor-pane';

export function EditorSplitView({ layout }: { layout: LayoutNode }) {
  if (layout.type === 'pane') {
    return <EditorPane paneId={layout.paneId} />;
  }

  const isRow = layout.direction === 'row';

  return (
    <div className={`flex h-full min-h-0 min-w-0 flex-1 ${isRow ? 'flex-row' : 'flex-col'}`}>
        <div className={`flex h-full flex-1 ${isRow ? 'border-r' : 'border-b'} border-border`}>
            <EditorSplitView layout={layout.children[0]} />
        </div>

        <div className="flex h-full flex-1">
            <EditorSplitView layout={layout.children[1]} />
        </div>
    </div>
  );
}
