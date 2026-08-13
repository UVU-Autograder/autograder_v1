import { useEffect, useState } from "react";
import { Editor, type EditorProps } from "@monaco-editor/react";

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