import { useEffect, useState } from "react";
import { Editor, loader, type EditorProps } from "@monaco-editor/react";

// Serve Monaco from this app (public/monaco/vs, copied by scripts/copy-monaco.mjs)
// rather than the jsdelivr default, which some networks block.
loader.config({ paths: { vs: "/monaco/vs" } });

export default function MonacoEditor({
  height = "100%",
  width = "100%",
  defaultLanguage = "python",
  defaultValue = "",
  value,
  language,
  onChange,
  onMount,
  options,
  theme,
}: {
  height?: string;
  width?: string;
  defaultLanguage?: string;
  defaultValue?: string;
  value?: string;
  language?: string;
  onChange?: (value: string | undefined) => void;
  onMount?: EditorProps["onMount"];
  options?: EditorProps["options"];
  theme?: string;
}) {
  const [editorTheme, setEditorTheme] = useState<"vs" | "vs-dark">(() =>
    typeof window !== "undefined" && document.documentElement.classList.contains("dark") ? "vs-dark" : "vs"
  );
  const [loadFailed, setLoadFailed] = useState(false);

  useEffect(() => {
    const updateTheme = () => {
      const isDark = document.documentElement.classList.contains("dark");
      setEditorTheme(isDark ? "vs-dark" : "vs");
    };

    updateTheme();

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === "class") {
          updateTheme();
        }
      });
    });

    observer.observe(document.documentElement, { attributes: true });

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let cancelled = false;
    loader.init().catch(() => {
      if (!cancelled) setLoadFailed(true);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loadFailed) {
    // Plain editor so students can still edit and run when Monaco cannot load.
    return (
      <textarea
        aria-label="Code editor"
        data-testid="editor-fallback"
        className="h-full w-full resize-none bg-background p-3 font-mono text-sm outline-none"
        style={{ height, width }}
        spellCheck={false}
        readOnly={Boolean(options?.readOnly)}
        defaultValue={value === undefined ? defaultValue : undefined}
        value={value}
        onChange={(event) => onChange?.(event.target.value)}
      />
    );
  }

  return (
    <Editor
      height={height}
      width={width}
      theme={theme || editorTheme}
      language={language || defaultLanguage}
      defaultValue={defaultValue}
      value={value}
      onChange={onChange}
      onMount={onMount}
      options={{
        automaticLayout: true,
        scrollBeyondLastLine: false,
        minimap: { enabled: false },
        ...options,
      }}
    />
  );
}
