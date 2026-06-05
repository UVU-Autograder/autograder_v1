import { TerminalSquareIcon, BotIcon, BookOpenIcon, Settings2Icon } from "lucide-react"
import { AppSidebar } from "@/components/app-sidebar"

const data = {
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
                url: "#",
            },
            {
                title: "Test Case 2",
                url: "#",
            }
            ],
        },
        {
            title: "Files",
            url: "#",
            icon: (
            <BookOpenIcon
            />
            ),
            items: [
            {
                title: "main.py",
                url: "#",
            },
            {
                title: "test_main.py",
                url: "#",
            },
            {
                title: "requirements.txt",
                url: "#",
            }
            ],
        },
        {
            title: "Constraints",
            url: "#",
            icon: (
            <Settings2Icon
            />
            ),
            items: [
            {
                title: "No Bubble Sort",
                url: "#",
            },
            ],
        },
    ]
}

export function AssignmentsSidebar() {
    return (
        <AppSidebar data={data} />
    )
}