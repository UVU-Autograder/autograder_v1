import { Editor, type EditorProps } from "@monaco-editor/react";

export default function MonacoEditor({
  height = "100%",
  width = "100%",
  defaultLanguage = "python",
  defaultValue = "",
  value,
  language,
  onChange,
  options,
}: {
  height?: string;
  width?: string;
  defaultLanguage?: string;
  defaultValue?: string;
  value?: string;
  language?: string;
  onChange?: (value: string | undefined) => void;
  options?: EditorProps["options"];
}) {
  return (
    <Editor
      height={height}
      width={width}
      language={language || defaultLanguage}
      defaultValue={defaultValue}
      value={value}
      onChange={onChange}
      options={options}
    />
  );
}