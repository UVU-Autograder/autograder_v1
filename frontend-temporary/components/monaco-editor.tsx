import { Editor } from "@monaco-editor/react";

export default function MonacoEditor({ height, width, defaultLanguage, defaultValue, className = "" }: { height: string, width: string, defaultLanguage: string, defaultValue: string, className?: string }) {
  return (
    <div className={className || ""}>
      <Editor 
        height={height} 
        width={width}
        defaultLanguage={defaultLanguage} 
        defaultValue={defaultValue}
      />
    </div>
    );
}