"use client"

import { Header } from "@/components/header"
import { DemoSection } from "@/components/demo-section"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { FileText, Zap, Shield, BarChart, Download } from "lucide-react"

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 md:py-24">
        <div className="flex flex-col items-center text-center space-y-8">
          <div className="space-y-4">
            <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl md:text-6xl lg:text-7xl">
              CSV Charset
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                {" "}Analysis
              </span>
            </h1>
            <p className="mx-auto max-w-[700px] text-lg text-muted-foreground md:text-xl">
              Python tool for CSV character encoding detection and conversion. 
              See it in action with the demo, then download for private local processing.
            </p>
          </div>
          
          <div className="flex flex-col gap-4 sm:flex-row">
            <Button size="lg" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700" onClick={() => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })}>
              <Zap className="mr-2 h-4 w-4" />
              See Live Demo
            </Button>
            <Button variant="outline" size="lg" onClick={() => window.location.href = '/download'}>
              <Download className="mr-2 h-4 w-4" />
              Download Python Tool
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="container mx-auto px-4 py-16">
        <div className="space-y-8">
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-bold tracking-tighter md:text-4xl">
              Powerful Features
            </h2>
            <p className="mx-auto max-w-[600px] text-muted-foreground md:text-lg">
              Everything you need for character encoding detection and conversion
            </p>
          </div>
          
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <Card className="border-2 hover:shadow-lg transition-shadow">
              <CardHeader>
                <Zap className="h-8 w-8 text-blue-600" />
                <CardTitle>Lightning Fast</CardTitle>
                <CardDescription>
                  Parallel processing with smart job management for optimal performance
                </CardDescription>
              </CardHeader>
            </Card>
            
            <Card className="border-2 hover:shadow-lg transition-shadow">
              <CardHeader>
                <Shield className="h-8 w-8 text-green-600" />
                <CardTitle>Safe & Secure</CardTitle>
                <CardDescription>
                  Automatic backups, dry-run mode, and rollback capabilities
                </CardDescription>
              </CardHeader>
            </Card>
            
            <Card className="border-2 hover:shadow-lg transition-shadow">
              <CardHeader>
                <BarChart className="h-8 w-8 text-purple-600" />
                <CardTitle>Detailed Analytics</CardTitle>
                <CardDescription>
                  Comprehensive encoding statistics and success rates
                </CardDescription>
              </CardHeader>
            </Card>
            
            <Card className="border-2 hover:shadow-lg transition-shadow">
              <CardHeader>
                <FileText className="h-8 w-8 text-orange-600" />
                <CardTitle>Multiple Formats</CardTitle>
                <CardDescription>
                  Support for UTF-8, ASCII, ISO-8859-*, Windows-125x, and more
                </CardDescription>
              </CardHeader>
            </Card>
            
            <Card className="border-2 hover:shadow-lg transition-shadow">
              <CardHeader>
                <Download className="h-8 w-8 text-red-600" />
                <CardTitle>Batch Conversion</CardTitle>
                <CardDescription>
                  Convert multiple files with filtering and preview options
                </CardDescription>
              </CardHeader>
            </Card>
            
            <Card className="border-2 hover:shadow-lg transition-shadow">
              <CardHeader>
                <Shield className="h-8 w-8 text-indigo-600" />
                <CardTitle>Local Processing</CardTitle>
                <CardDescription>
                  Python tool runs locally - web interface for demonstration
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* Demo Section */}
      <div id="demo">
        <DemoSection />
      </div>

      {/* About Section */}
      <section id="about" className="bg-muted/50 py-16">
        <div className="container mx-auto px-4">
          <div className="grid gap-8 lg:grid-cols-2 items-center">
            <div className="space-y-6">
              <h2 className="text-3xl font-bold tracking-tighter md:text-4xl">
                About the Tool
              </h2>
              <div className="space-y-4 text-muted-foreground">
                <p>
                  This modern web interface provides an intuitive way to detect and convert 
                  character encodings in CSV files. Built with Next.js and Tailwind CSS, 
                  it offers a clean, responsive design with full dark mode support.
                </p>
                <p>
                  The underlying Python engine uses advanced heuristics and parallel 
                  processing to quickly and accurately identify file encodings, making 
                  it perfect for data scientists and developers working with diverse datasets.
                </p>
              </div>
            </div>
            
            <Card className="bg-card">
              <CardHeader>
                <CardTitle>Quick Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Supported Encodings</span>
                  <span className="font-semibold">15+</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Processing Speed</span>
                  <span className="font-semibold">Parallel</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Data Privacy</span>
                  <span className="font-semibold">100% Offline</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Backup Safety</span>
                  <span className="font-semibold">Automatic</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 mt-auto">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span className="font-semibold">Charset Analysis Tool</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Built with Next.js, Tailwind CSS, and modern web technologies.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
