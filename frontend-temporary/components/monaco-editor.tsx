import { Editor } from "@monaco-editor/react";

export default function MonacoEditor({
  height, width, defaultLanguage, defaultValue, className, onChange
}: {
  height: string;
  width: string;
  defaultLanguage: string;
  defaultValue: string;
  className?: string;
  onChange?: (value: string | undefined) => void;
}) {
  return (
    <Editor
      height={height}
      width={width}
      defaultLanguage={defaultLanguage}
      defaultValue={defaultValue}
      onChange={onChange}
      options={{ minimap: { enabled: false } }}  // optional, more IDE-like
    />
  );
}