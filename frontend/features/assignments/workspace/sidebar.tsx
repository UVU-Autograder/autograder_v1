'use client';

import Link from "next/link";
import { ArrowLeftIcon, TerminalSquareIcon, BookOpenIcon } from "lucide-react"
import { Button } from "@/components/ui/button";
import { AppSidebar } from "@/components/app-sidebar"
import { Assignment } from "@/features/assignments/types";
import { useAssignmentFile } from "./assignment-file-context";
import { FileUploadButton } from "./file-upload-button";
import { useBasePath } from "@/lib/view-context";

function detailsFileContent(assignment: Assignment) {
    const constraintsList = (assignment.constraints || [])
        .map((c) => `- ${c.label}: ${c.value}`)
        .join("\n") || "None";

    return `Assignment Details: ${assignment.title}
==================================================

Max Score: ${assignment.max_score} points

Submission Rules & Constraints:
${constraintsList}

Allowed Concepts:
-----------------
${(assignment.allowed_concepts || []).map(c => `- ${c}`).join("\n") || "No concepts whitelist configured (all concepts allowed)."}
`;
}

export function AssignmentSidebar({
    assignment,
    courseId,
    className
}: {
    assignment: Assignment;
    courseId: string;
    className: string
}) {
    const basePath = useBasePath();
    const { files, openFileByName, uploadFiles, deleteFile } = useAssignmentFile();
    const workspaceFiles = Object.values(files)
        .filter((file) => file.category === 'workspace')
        .map((file) => file.filename)
        .sort((a, b) => a.localeCompare(b));

    const data = {
        header: (
            <Button variant="ghost" size="sm" className="w-full justify-start" asChild>
                <Link href={basePath === "/sandbox" ? `/sandbox/${courseId}` : `/staff/courses/${courseId}`}>
                    <ArrowLeftIcon />
                    Back to assignments
                </Link>
            </Button>
        ),
        navMain: [
            {
                title: "Details",
                url: "#",
                icon: (
                <TerminalSquareIcon
                />
                ),
                isActive: true,
                items: [
                    {
                        title: "details.txt",
                        onClick: () =>
                            openFileByName("details.txt", {
                                content: detailsFileContent(assignment),
                                language: 'plaintext',
                                category: 'constraint',
                            }),
                    }
                ]
            },
            {
                title: "Files",
                url: "#",
                isActive: true,
                icon: (
                <BookOpenIcon
                />
                ),
                items: workspaceFiles.map((filename) => ({
                    title: filename,
                    onClick: () => openFileByName(filename),
                    onDelete: () => deleteFile(filename),
                })),
                actions: (
                    <FileUploadButton
                        className="w-full"
                        onFilesSelected={uploadFiles}
                    />
                ),
            },
        ]
    }

    return (
        <AppSidebar data={data} className={className} />
    )
}
