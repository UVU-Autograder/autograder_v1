"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { PlusCircleIcon, Trash2Icon, PlusIcon, XIcon } from "lucide-react";
import { useAssignmentEditor } from "./assignment-editor-context";

export function MetadataSection() {
  const {
    title,
    setTitle,
    moduleId,
    setModuleId,
    sandboxEnabled,
    setSandboxEnabled,
    language,
    courseModules,
    entrypoint,
    setEntrypoint,
    fileRequirements,
    addFileRequirement,
    removeFileRequirement,
    updateFileRequirement,
    updateFileRequirementPath,
    addFileRequirementPath,
    removeFileRequirementPath,
    toggleFileRequirementGlob,
    markDirty,
  } = useAssignmentEditor();

  return (
    <div className="space-y-6">
      {/* Basic General Metadata Card */}
      <Card>
        <CardHeader>
          <CardTitle>General Metadata</CardTitle>
          <CardDescription>Configure basic assignment information and course module assignment.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Assignment Title *</label>
              <Input
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  markDirty();
                }}
                placeholder="e.g. Lab 1: Functions & Control Flow"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Module Assignment</label>
              <Select
                value={moduleId !== null ? String(moduleId) : "none"}
                onValueChange={(val) => {
                  setModuleId(val === "none" ? null : parseInt(val, 10));
                  markDirty();
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="No Module" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No Module</SelectItem>
                  {courseModules.map((m) => (
                    <SelectItem key={m.id} value={String(m.id)}>
                      {m.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Programming Language</label>
              <Input value={language} disabled className="bg-slate-100 font-mono text-slate-500 capitalize" />
            </div>
          </div>

          <div className="flex items-center space-x-2 pt-4 border-t border-slate-100">
            <input
              type="checkbox"
              id="sandbox"
              checked={sandboxEnabled}
              onChange={(e) => {
                setSandboxEnabled(e.target.checked);
                markDirty();
              }}
              className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            />
            <label htmlFor="sandbox" className="text-sm font-semibold text-slate-700 cursor-pointer">
              Enable Student Sandbox Access
            </label>
          </div>
        </CardContent>
      </Card>

      {/* File Requirements Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div>
            <CardTitle>File Requirements</CardTitle>
            <CardDescription className="mt-1">
              Set up required files and select which file serves as the primary execution entrypoint.
            </CardDescription>
          </div>
          <Button type="button" onClick={addFileRequirement} variant="outline" size="sm">
            <PlusCircleIcon className="w-4 h-4 mr-1.5" /> Add Required File
          </Button>
        </CardHeader>
        <CardContent className="space-y-6 pt-4">
          <div className="space-y-4">
            {fileRequirements.map((req, idx) => {
              const isEntrypoint = Boolean(
                (req.paths && req.paths.includes(entrypoint)) || req.pattern === entrypoint
              );

              return (
                <div
                  key={idx}
                  className={`relative rounded-lg border p-4 shadow-xs space-y-4 transition-colors ${
                    isEntrypoint ? "border-indigo-300 bg-indigo-50/30" : "border-slate-200 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <label className="flex items-center gap-2 cursor-pointer font-semibold text-xs text-slate-700">
                      <input
                        type="radio"
                        name="entrypoint_selection"
                        checked={isEntrypoint}
                        onChange={() => {
                          const targetPath = req.paths?.[0] || req.pattern || "";
                          if (targetPath) {
                            setEntrypoint(targetPath);
                            markDirty();
                          }
                        }}
                        className="w-4 h-4 text-indigo-600 focus:ring-indigo-500"
                      />
                      <span>Primary Entrypoint</span>
                    </label>
                    <button
                      type="button"
                      onClick={() => removeFileRequirement(idx)}
                      className="text-slate-400 hover:text-red-500 transition-colors p-1 cursor-pointer"
                    >
                      <Trash2Icon className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-500 uppercase">Label / Rule Name *</label>
                    <Input
                      value={req.label || ""}
                      onChange={(e) => updateFileRequirement(idx, "label", e.target.value)}
                      placeholder="e.g. Main Entrypoint Script"
                      className="text-xs"
                    />
                  </div>

                  <div className="space-y-2 pt-2 border-t border-slate-100">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-semibold text-slate-500 uppercase">
                        {req.pattern !== undefined && req.pattern !== null ? "Glob Pattern" : "Allowed File Name(s)"}
                      </label>
                      <label className="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={req.pattern !== undefined && req.pattern !== null}
                          onChange={(e) => toggleFileRequirementGlob(idx, e.target.checked)}
                          className="w-3.5 h-3.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <span>Treat as glob pattern (e.g. *.py, lab?.txt)</span>
                      </label>
                    </div>

                    {req.pattern !== undefined && req.pattern !== null ? (
                      <div className="space-y-1">
                        <Input
                          value={req.pattern}
                          onChange={(e) => {
                            updateFileRequirement(idx, "pattern", e.target.value);
                            if (isEntrypoint) {
                              setEntrypoint(e.target.value);
                            }
                          }}
                          placeholder="e.g. *.py"
                          className="font-mono text-xs max-w-md"
                        />
                        <p className="text-[11px] text-slate-400">
                          Evaluated using Python&apos;s <code className="font-mono bg-slate-100 px-1 py-0.5 rounded text-slate-600">Path.glob()</code> syntax (use <code className="font-mono bg-slate-100 px-1 py-0.5 rounded text-slate-600">**/*.py</code> for recursive subfolders).
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {(req.paths || [""]).map((path, pathIdx) => (
                          <div key={pathIdx} className="flex gap-2 items-center">
                            <Input
                              value={path}
                              onChange={(e) => {
                                updateFileRequirementPath(idx, pathIdx, e.target.value);
                                if (isEntrypoint && pathIdx === 0) {
                                  setEntrypoint(e.target.value);
                                }
                              }}
                              placeholder={pathIdx === 0 ? "e.g. main.py" : "e.g. solution.py"}
                              className="font-mono text-xs max-w-md"
                            />
                            {(req.paths?.length || 0) > 1 && (
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() => removeFileRequirementPath(idx, pathIdx)}
                              >
                                <XIcon className="w-3.5 h-3.5 text-slate-400 hover:text-red-500" />
                              </Button>
                            )}
                          </div>
                        ))}

                        <div className="flex flex-wrap items-center gap-4 pt-1">
                          <Button
                            type="button"
                            onClick={() => addFileRequirementPath(idx)}
                            variant="outline"
                            size="sm"
                            className="h-7 text-xs text-indigo-600 border-indigo-200 hover:bg-indigo-50"
                          >
                            <PlusIcon className="w-3 h-3 mr-1" /> Add Alternate File Name
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {fileRequirements.length === 0 && (
              <div className="rounded-lg border border-dashed border-slate-200 p-8 text-center">
                <p className="text-sm font-medium text-slate-600">No file requirements configured.</p>
                <p className="text-xs text-slate-400 mt-1 mb-4">Add at least one required file to configure execution.</p>
                <Button type="button" onClick={addFileRequirement} variant="outline" size="sm">
                  <PlusCircleIcon className="w-4 h-4 mr-1.5" /> Add Required File
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
