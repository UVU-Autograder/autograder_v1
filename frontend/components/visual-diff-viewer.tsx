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
        <div key={`equal-${i}`} className="px-4 py-0.5 text-slate-400 font-mono text-xs select-none">
          <span className="w-6 inline-block text-slate-600 select-none">{i + 1}</span>
          <span className="text-slate-300">  {expLine}</span>
        </div>
      );
    } else {
      if (expLine !== undefined) {
        diffLines.push(
          <div key={`del-${i}`} className="px-4 py-0.5 bg-rose-950/30 text-rose-400 font-mono text-xs border-l-2 border-rose-500">
            <span className="w-6 inline-block text-rose-700/60 select-none">{i + 1}</span>
            <span>- {expLine}</span>
          </div>
        );
      }
      if (actLine !== undefined) {
        diffLines.push(
          <div key={`add-${i}`} className="px-4 py-0.5 bg-emerald-950/30 text-emerald-400 font-mono text-xs border-l-2 border-emerald-500">
            <span className="w-6 inline-block text-emerald-700/60 select-none">{i + 1}</span>
            <span>+ {actLine}</span>
          </div>
        );
      }
    }
  }

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/90 overflow-hidden shadow-inner">
      <div className="bg-slate-900 px-4 py-2 border-b border-slate-800 flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase tracking-wider select-none">
        <span>Output Difference</span>
        <div className="flex gap-3">
          <span className="flex items-center gap-1 text-rose-400"><span className="size-2 rounded-full bg-rose-500"></span> Expected</span>
          <span className="flex items-center gap-1 text-emerald-400"><span className="size-2 rounded-full bg-emerald-500"></span> Student</span>
        </div>
      </div>
      <div className="py-2 overflow-x-auto max-h-96 whitespace-pre">
        {diffLines}
      </div>
    </div>
  );
}
