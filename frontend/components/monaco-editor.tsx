import { Editor } from "@monaco-editor/react";

export default function MonacoEditor({
  height, width, defaultLanguage, defaultValue, onChange, options
}: {
  height: string;
  width: string;
  defaultLanguage: string;
  defaultValue: string;
  onChange?: (value: string | undefined) => void;
  options?: any;
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