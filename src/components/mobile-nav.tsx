"use client"

import * as React from "react"
import { Menu } from "lucide-react"
import { Button } from "@/components/ui/button"

export function MobileNav() {
  const [open, setOpen] = React.useState(false)

  return (
    <div className="flex md:hidden">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setOpen(!open)}
        className="mr-2"
      >
        <Menu className="h-5 w-5" />
        <span className="sr-only">Toggle menu</span>
      </Button>
      
      {open && (
        <div className="fixed inset-0 top-14 z-50 grid h-[calc(100vh-3.5rem)] grid-flow-row auto-rows-max overflow-auto p-6 pb-32 shadow-md animate-in slide-in-from-bottom-80 md:hidden">
          <div className="relative z-20 grid gap-6 rounded-md bg-popover p-4 text-popover-foreground shadow-md">
            <nav className="grid grid-flow-row auto-rows-max text-sm">
              <a
                href="#demo"
                className="flex w-full items-center rounded-md p-2 text-sm font-medium hover:underline"
                onClick={() => setOpen(false)}
              >
                Demo
              </a>
              <a
                href="#features"
                className="flex w-full items-center rounded-md p-2 text-sm font-medium hover:underline"
                onClick={() => setOpen(false)}
              >
                Features
              </a>
              <a
                href="#about"
                className="flex w-full items-center rounded-md p-2 text-sm font-medium hover:underline"
                onClick={() => setOpen(false)}
              >
                About
              </a>
              <a
                href="/download"
                className="flex w-full items-center rounded-md p-2 text-sm font-medium hover:underline"
                onClick={() => setOpen(false)}
              >
                Download
              </a>
            </nav>
          </div>
        </div>
      )}
    </div>
  )
}