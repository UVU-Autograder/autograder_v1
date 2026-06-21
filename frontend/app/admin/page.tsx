"use client"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger} from "../../components/ui/accordion"
import {Dialog, DialogContent, DialogFooter, 
  DialogDescription, DialogHeader, DialogTitle, } from "../../components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useState } from "react"


type Person = "instructors" | "ias" | "students"


export default function AdminPage () {
    const [open, setOpen] = useState(false)
    const [section, setSection] = useState<Person>("instructors")
    const [name, setName] = useState("")
    const [instructors, setInstructors] = useState<string[]>([])
    const [ias, setIas] = useState<string[]>([])
    const [students, setStudents] = useState<string[]>([])

    function openDialog(target: Person) {
        setSection(target)
        setName("")
        setOpen(true)
    }

    function savePerson() {
        if (!name.trim()) return

        if (section === "instructors") {
        setInstructors((prev) => [...prev, name.trim()])
        } else if (section === "ias") {
        setIas((prev) => [...prev, name.trim()])
        } else {
        setStudents((prev) => [...prev, name.trim()])
        }
        setOpen(false)
    }
    return (
    <div>
        <h1 className="flex justify-center text-xl">Admin</h1>
        <div className="flex">
            <div className="flex flex-col mt-10 ml-10">
                <Accordion type="single" collapsible>
                    <AccordionItem value="instructors">
                        <AccordionTrigger className="text-base">
                            <span>Instructors</span>
                        </AccordionTrigger>
                        <AccordionContent>
                            {instructors.map((person, index) => (
                                <div key={`${person}-${index}`}>{person}</div>
                            ))}
                        </AccordionContent>
                    </AccordionItem>
                </Accordion>
                <Accordion type="single" collapsible>
                    <AccordionItem value="instructors">
                        <AccordionTrigger className="text-base">
                            <span>Instructional Assistants</span>
                        </AccordionTrigger>
                        <AccordionContent>
                            {ias.map((person, index) => (
                                <div key={`${person}-${index}`}>{person}</div>
                            ))}
                        </AccordionContent>
                    </AccordionItem>
                </Accordion>
                <Accordion type="single" collapsible>
                    <AccordionItem value="instructors">
                        <AccordionTrigger className="text-base">
                            <span>Students</span>
                        </AccordionTrigger>
                        <AccordionContent>
                            {students.map((person, index) => (
                                <div key={`${person}-${index}`}>{person}</div>
                            ))}
                        </AccordionContent>
                    </AccordionItem>
                </Accordion>
            </div>
                <div className="flex flex-col gap-5 mt-12 ml-2">
                    <Button className="text-base font-bold px-4 py-2" size="sm"
                     onClick={() => openDialog("instructors")}>+</Button>
                    <Button className="text-base font-bold px-4 py-2" size="sm"
                     onClick={() => openDialog("ias")}>+</Button>
                    <Button className="text-base font-bold px-4 py-2" size="sm"
                     onClick={() => openDialog("students")}>+</Button>
                </div>
                <Dialog open={open} onOpenChange={setOpen}>
                    <DialogContent aria-describedby={undefined}>
                      <DialogHeader>
                          <DialogTitle>Add person</DialogTitle>
                      </DialogHeader>
                      <Input
                          value={name}
                          onChange={(e) => setName(e.target.value)}
                          placeholder="Enter name"
                      />
                      <DialogFooter>
                          <Button onClick={savePerson}>Save</Button>
                      </DialogFooter>
                    </DialogContent>
                </Dialog>
        </div>
    </div>
    )
}
