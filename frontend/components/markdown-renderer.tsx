"use client";

import React from "react";
import ReactMarkdown from "react-markdown";

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
      className={`text-xs text-foreground font-sans leading-relaxed space-y-2.5 ${className}`}
    >
      <ReactMarkdown
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
          h1: ({ children }) => (
            <h4 className="font-bold text-sm text-foreground mt-2 mb-1">{children}</h4>
          ),
          h2: ({ children }) => (
            <h5 className="font-bold text-xs text-foreground mt-2 mb-1">{children}</h5>
          ),
          h3: ({ children }) => (
            <h6 className="font-semibold text-xs text-foreground mt-1 mb-0.5">{children}</h6>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
