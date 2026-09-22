import React from "react";

interface VisualDiffViewerProps {
  expected?: string | null;
  actual?: string | null;
}

export default function VisualDiffViewer({ expected, actual }: VisualDiffViewerProps) {
  const expectedStr = expected ?? "";
  const actualStr = actual ?? "";
  const expectedLines = expectedStr.split(/\r?\n/);
  const actualLines = actualStr.split(/\r?\n/);
  const maxLines = Math.max(expectedLines.length, actualLines.length);

  const diffLines: React.ReactNode[] = [];

  for (let i = 0; i < maxLines; i++) {
    const expLine = expectedLines[i];
    const actLine = actualLines[i];

    if (expLine === actLine) {
      diffLines.push(
        <div key={`equal-${i}`} className="px-3.5 py-0.5 text-muted-foreground font-mono text-xs select-none">
          <span className="w-6 inline-block text-muted-foreground/50 select-none">{i + 1}</span>
          <span className="text-foreground/90">  {expLine}</span>
        </div>
      );
    } else {
      if (expLine !== undefined) {
        diffLines.push(
          <div key={`del-${i}`} className="px-3.5 py-0.5 bg-destructive/10 text-destructive font-mono text-xs border-l-2 border-destructive">
            <span className="w-6 inline-block text-destructive/60 select-none">{i + 1}</span>
            <span>- {expLine}</span>
          </div>
        );
      }
      if (actLine !== undefined) {
        diffLines.push(
          <div key={`add-${i}`} className="px-3.5 py-0.5 bg-success/10 text-success font-mono text-xs border-l-2 border-success">
            <span className="w-6 inline-block text-success/60 select-none">{i + 1}</span>
            <span>+ {actLine}</span>
          </div>
        );
      }
    }
  }

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden shadow-xs">
      <div className="bg-muted/60 px-3.5 py-2 border-b border-border flex justify-between items-center text-xs font-semibold text-muted-foreground uppercase tracking-wider select-none">
        <span>Output Difference</span>
        <div className="flex gap-3">
          <span className="flex items-center gap-1.5 text-destructive font-medium"><span className="size-2 rounded-full bg-destructive"></span> Expected</span>
          <span className="flex items-center gap-1.5 text-success font-medium"><span className="size-2 rounded-full bg-success"></span> Student</span>
        </div>
      </div>
      <div className="py-2 overflow-x-auto max-h-96 whitespace-pre font-mono">
        {diffLines}
      </div>
    </div>
  );
}
