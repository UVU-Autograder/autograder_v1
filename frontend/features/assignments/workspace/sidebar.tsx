'use client';

import Link from "next/link";
import { ArrowLeftIcon, TerminalSquareIcon, BotIcon, BookOpenIcon, Settings2Icon } from "lucide-react"
import { Button } from "@/components/ui/button";
import { AppSidebar } from "@/components/app-sidebar"
import { Assignment, Constraint } from "@/features/assignments/types";
import { useAssignmentFile } from "./assignment-file-context";
import { FileUploadButton } from "./file-upload-button";
import { useBasePath } from "@/lib/view-context";

function constraintFilename(label: string) {
    return `${label.toLowerCase().replace(/\s+/g, '_').replace(/[^\w.-]/g, '')}.txt`;
}

function constraintFileContent(constraint: Constraint) {
    return `${constraint.label}\n${'='.repeat(constraint.label.length)}\n\n${constraint.value}`;
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
    const { files, openFileByName, uploadFiles } = useAssignmentFile();
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
            },
            {
                title: "Test Cases",
                url: "#",
                icon: (
                <BotIcon
                />
                ),
                items: [
                {
                    title: "Test Case 1",
                    onClick: () =>
                        openFileByName("test_case_1.txt", { category: 'test_case' }),
                },
                {
                    title: "Test Case 2",
                    onClick: () =>
                        openFileByName("test_case_2.txt", { category: 'test_case' }),
                }
                ],
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
                })),
                actions: (
                    <FileUploadButton
                        className="w-full"
                        onFilesSelected={uploadFiles}
                    />
                ),
            },
            {
                title: "Constraints",
                url: "#",
                icon: (
                <Settings2Icon
                />
                ),
                items: assignment.constraints.map((constraint) => ({
                    title: constraint.label,
                    onClick: () =>
                        openFileByName(constraintFilename(constraint.label), {
                            content: constraintFileContent(constraint),
                            language: 'plaintext',
                            category: 'constraint',
                        }),
                })),
            },
        ]
    }

    return (
        <AppSidebar data={data} className={className} />
    )
}
