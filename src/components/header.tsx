"use client"

import Link from "next/link"
import { FileText, Github } from "lucide-react"
import { ThemeToggle } from "./theme-toggle"
import { MobileNav } from "./mobile-nav"
import { Button } from "./ui/button"

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 max-w-screen-2xl items-center">
        <div className="mr-4 flex">
          <Link className="mr-6 flex items-center space-x-2" href="/">
            <FileText className="h-6 w-6" />
            <span className="hidden font-bold sm:inline-block">
              Charset Analysis
            </span>
          </Link>
          <nav className="hidden md:flex items-center gap-4 text-sm lg:gap-6">
            <a
              className="transition-colors hover:text-foreground/80 text-foreground/60"
              href="#demo"
            >
              Demo
            </a>
            <a
              className="transition-colors hover:text-foreground/80 text-foreground/60"
              href="#features"
            >
              Features
            </a>
            <a
              className="transition-colors hover:text-foreground/80 text-foreground/60"
              href="#about"
            >
              About
            </a>
            <a
              className="transition-colors hover:text-foreground/80 text-foreground/60"
              href="/download"
            >
              Download
            </a>
          </nav>
        </div>
        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <div className="w-full flex-1 md:w-auto md:flex-none">
            <Button 
              variant="outline" 
              className="hidden sm:flex ml-auto mr-2"
              onClick={() => window.open('https://github.com/xmxtxx/Charset_analysis', '_blank')}
            >
              <Github className="mr-2 h-4 w-4" />
              GitHub
            </Button>
          </div>
          <nav className="flex items-center space-x-2">
            <MobileNav />
            <ThemeToggle />
          </nav>
        </div>
      </div>
    </header>
  )
}