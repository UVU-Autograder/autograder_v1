"use client"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger} from "@/components/ui/accordion"
import {Dialog, DialogContent, DialogFooter, 
  DialogHeader, DialogTitle, } from "@/components/ui/dialog"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useState } from "react"

type Person = "instructors" | "ias" | "students"

export default function AccessPage () {
    const [open, setOpen] = useState(false)
    const [section, setSection] = useState<Person>("instructors")
    const [name, setName] = useState("")
    const [instructors, setInstructors] = useState<string[]>([])
    const [ias, setIas] = useState<string[]>([])
    const [students, setStudents] = useState<string[]>([])

    const openDialog = (target: Person) => {
        setSection(target)
        setName("")
        setOpen(true)
    }
    const savePerson = () => {
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
    const deletePerson = (section: Person, index: number) => {
      if (section === "instructors") {
        setInstructors((prev) => prev.filter((_, i) => i !== index))
      } else if (section === "ias") {
        setIas((prev) => prev.filter((_, i) => i !== index))
      } else {
        setStudents((prev) => prev.filter((_, i) => i !== index))
      }
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
                        {instructors.length > 0 && (
                        <AccordionContent>
                          <div className="flex flex-col gap-1">
                            {instructors.map((person, index) => (
                              <div
                                key={`${person}-${index}`}
                                className="flex items-center gap-2"
                              >
                                <span>{person}</span>
                                <Button
                                  variant="destructive"
                                  size="sm"
                                  onClick={() => deletePerson("instructors", index)}
                                >
                                  Remove
                                </Button>
                              </div>
                            ))}
                          </div>
                        </AccordionContent>
                      )}
                    </AccordionItem>
                </Accordion>
                <Accordion type="single" collapsible>
                    <AccordionItem value="instructors">
                        <AccordionTrigger className="text-base">
                            <span>Instructional Assistants</span>
                        </AccordionTrigger>
                          {ias.length > 0 && (
                          <AccordionContent>
                            <div className="flex flex-col gap-1">
                              {ias.map((person, index) => (
                                <div
                                  key={`${person}-${index}`}
                                  className="flex items-center gap-2"
                                >
                                  <span>{person}</span>
                                  <Button
                                    variant="destructive"
                                    size="sm"
                                    onClick={() => deletePerson("ias", index)}
                                  >
                                    Remove
                                  </Button>
                                </div>
                              ))}
                            </div>
                          </AccordionContent>
                        )}
                    </AccordionItem>
                </Accordion>
                <Accordion type="single" collapsible>
                    <AccordionItem value="instructors">
                        <AccordionTrigger className="text-base">
                            <span>Students</span>
                        </AccordionTrigger>
                            {students.length > 0 && (
                            <AccordionContent>
                              <div className="flex flex-col gap-1">
                                {students.map((person, index) => (
                                  <div
                                    key={`${person}-${index}`}
                                    className="flex items-center gap-2"
                                  >
                                    <span>{person}</span>
                                    <Button
                                      variant="destructive"
                                      size="sm"
                                      onClick={() => deletePerson("students", index)}
                                    >
                                      Remove
                                    </Button>
                                  </div>
                                ))}
                              </div>
                            </AccordionContent>
                          )}
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
