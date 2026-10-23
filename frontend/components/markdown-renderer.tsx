"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export default function MarkdownRenderer({
  content,
  className = "",
}: MarkdownRendererProps) {
  return (
    <div
      className={`text-xs text-foreground font-sans leading-relaxed space-y-1.5 ${className}`}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
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
        {content}
      </ReactMarkdown>
    </div>
  );
}
