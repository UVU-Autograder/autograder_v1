import { Editor, type EditorProps } from "@monaco-editor/react";

export default function MonacoEditor({
  height, width, defaultLanguage, defaultValue, onChange, options
}: {
  height: string;
  width: string;
  defaultLanguage: string;
  defaultValue: string;
  onChange?: (value: string | undefined) => void;
  options?: EditorProps["options"];
}) {
  return (
    <Editor
      height={height}
      width={width}
      defaultLanguage={defaultLanguage}
      defaultValue={defaultValue}
      onChange={onChange}
      options={options}
    />
  );
}