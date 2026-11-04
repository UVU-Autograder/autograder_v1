"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

/**
 * Defensively cleans and normalizes raw markdown input to recover from common
 * scrape/export formatting anomalies (e.g. Canvas artifacts, glued code fences,
 * invisible zero-width spaces).
 */
export function normalizeMarkdownContent(content: string): string {
  if (!content) return "";

  let text = content
    // 1. Strip zero-width space characters and BOM
    .replace(/[\u200B-\u200D\uFEFF]/g, "")
    // 2. Strip Canvas download scrape artifacts (e.g. "Download filename.pyDownload Download filename.py")
    .replace(/(?:Download\s+[^\s\n]+\.[a-z0-9]+Download\s+Download\s+[^\s\n]+\.[a-z0-9]+|Download\s+[^\s\n]+\.[a-z0-9]+(?:Download)+)/gi, "")

  // 3. Fix glued opening code fence where code is on the fence delimiter line
  // e.g. "```def main():" -> "```python\ndef main():"
  text = text.replace(/^```([^\n`]+)$/gm, (match, info) => {
    const trimmed = info.trim();
    // Valid standard fence info string (single word language identifier)
    if (/^[a-z0-9_#+-]+$/i.test(trimmed)) {
      return match;
    }
    return "```python\n" + trimmed;
  });

  // 4. Fix glued closing code fence where ``` is attached to the end of a code line
  // e.g. "    main()```" -> "    main()\n```"
  text = text.replace(/^([^\n`]+)```$/gm, "$1\n```");

  return text;
}

export default function MarkdownRenderer({
  content,
  className = "",
}: MarkdownRendererProps) {
  const normalized = normalizeMarkdownContent(content);

  return (
    <div
      className={`text-xs text-foreground font-sans leading-relaxed space-y-1.5 ${className}`}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          pre: ({ children }) => <>{children}</>,
          p: ({ children }) => (
            <p className="leading-relaxed text-foreground">{children}</p>
          ),
          ul: ({ children }) => (
            <ul className="list-disc pl-4 space-y-1 text-foreground my-1.5">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-4 space-y-1 text-foreground my-1.5">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed">{children}</li>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-foreground">{children}</strong>
          ),
          em: ({ children }) => <em className="italic">{children}</em>,
          code: ({
            className: codeClassName,
            children,
            ...props
          }: React.HTMLAttributes<HTMLElement>) => {
            const isInline = !codeClassName && typeof children === "string" && !children.includes("\n");
            if (isInline) {
              return (
                <code
                  className="font-mono text-xs bg-muted/80 text-foreground px-1 py-0.5 rounded border border-border/60"
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <pre className="p-2.5 rounded-md bg-muted/60 border border-border text-foreground font-mono text-xs overflow-x-auto my-2">
                <code {...props}>{children}</code>
              </pre>
            );
          },
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-primary/50 pl-3 italic text-muted-foreground my-2">
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto rounded-md border border-border my-2">
              <table className="w-full border-collapse text-left text-xs">{children}</table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-muted/60 border-b border-border">{children}</thead>
          ),
          tr: ({ children }) => (
            <tr className="border-b border-border last:border-b-0">{children}</tr>
          ),
          th: ({ children, style }) => (
            <th className="px-2.5 py-1.5 align-top font-semibold text-foreground" style={style}>
              {children}
            </th>
          ),
          td: ({ children, style }) => (
            <td className="px-2.5 py-1.5 align-top text-foreground" style={style}>
              {children}
            </td>
          ),
          h1: ({ children }) => (
            <h4 className="mb-0.5 mt-2 font-bold text-sm text-foreground first:mt-0">
              {children}
            </h4>
          ),
          h2: ({ children }) => (
            <h5 className="mb-0.5 mt-2 font-bold text-xs text-foreground first:mt-0">
              {children}
            </h5>
          ),
          h3: ({ children }) => (
            <h6 className="mb-0.5 mt-1.5 font-semibold text-xs text-foreground first:mt-0">
              {children}
            </h6>
          ),
        }}
      >
        {normalized}
      </ReactMarkdown>
    </div>
  );
}
