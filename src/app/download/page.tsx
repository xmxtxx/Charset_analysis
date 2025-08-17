"use client"

import { Header } from "@/components/header"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, Terminal, Shield, Copy, Check } from "lucide-react"
import { useState } from "react"

export default function DownloadPage() {
  const [copied, setCopied] = useState<string | null>(null)

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopied(id)
    setTimeout(() => setCopied(null), 2000)
  }

  const installCommand = "pip3 install chardet"
  const usageCommand = "python3 check_csv_charset.py /path/to/your/csv/files"
  const helpCommand = "python3 check_csv_charset.py --help"

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      
      <div className="container mx-auto px-4 py-8">
        <div className="space-y-8">
          {/* Header */}
          <div className="text-center space-y-4">
            <h1 className="text-4xl font-bold tracking-tighter">
              Download CSV Charset Analysis Tool
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Get the Python script to analyze character encodings of your CSV files locally. 
              Your data stays on your machine - no uploads, no external processing.
            </p>
          </div>

          {/* Download Section */}
          <Card className="border-2 border-primary/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Download className="h-5 w-5" />
                Download Python Script
              </CardTitle>
              <CardDescription>
                Get the complete charset analysis tool for local use
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                size="lg" 
                className="w-full sm:w-auto"
                onClick={() => {
                  const link = document.createElement('a')
                  link.href = '/check_csv_charset.py'
                  link.download = 'check_csv_charset.py'
                  link.click()
                }}
              >
                <Download className="mr-2 h-4 w-4" />
                Download check_csv_charset.py
              </Button>
            </CardContent>
          </Card>

          {/* Installation Guide */}
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Terminal className="h-5 w-5" />
                  Installation
                </CardTitle>
                <CardDescription>
                  One-time setup to install required dependencies
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">1. Install Python Dependencies</h4>
                  <div className="bg-muted p-3 rounded-lg flex items-center justify-between">
                    <code className="text-sm">{installCommand}</code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(installCommand, 'install')}
                    >
                      {copied === 'install' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">2. Make Script Executable (Optional)</h4>
                  <div className="bg-muted p-3 rounded-lg">
                    <code className="text-sm">chmod +x check_csv_charset.py</code>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Privacy & Security
                </CardTitle>
                <CardDescription>
                  Why download instead of upload?
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-start gap-2">
                  <Shield className="h-4 w-4 mt-0.5 text-green-600" />
                  <div>
                    <p className="text-sm font-medium">100% Local Processing</p>
                    <p className="text-xs text-muted-foreground">Your CSV files never leave your computer</p>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <Shield className="h-4 w-4 mt-0.5 text-green-600" />
                  <div>
                    <p className="text-sm font-medium">No Data Transmission</p>
                    <p className="text-xs text-muted-foreground">No uploads, downloads, or network requests</p>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <Shield className="h-4 w-4 mt-0.5 text-green-600" />
                  <div>
                    <p className="text-sm font-medium">Open Source</p>
                    <p className="text-xs text-muted-foreground">Full transparency - review the code yourself</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Usage Examples */}
          <Card>
            <CardHeader>
              <CardTitle>Usage Examples</CardTitle>
              <CardDescription>Common ways to use the charset analysis tool</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-medium mb-2">Basic Analysis</h4>
                  <div className="bg-muted p-3 rounded-lg flex items-center justify-between">
                    <code className="text-sm text-wrap">{usageCommand}</code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(usageCommand, 'usage')}
                    >
                      {copied === 'usage' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">View All Options</h4>
                  <div className="bg-muted p-3 rounded-lg flex items-center justify-between">
                    <code className="text-sm">{helpCommand}</code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(helpCommand, 'help')}
                    >
                      {copied === 'help' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-medium">Advanced Examples:</h4>
                <div className="space-y-2 text-sm">
                  <div className="bg-muted p-2 rounded">
                    <code># Convert files to UTF-8 with backup</code><br/>
                    <code>python3 check_csv_charset.py data/ --convert-to utf-8</code>
                  </div>
                  <div className="bg-muted p-2 rounded">
                    <code># Fast scan of large dataset</code><br/>
                    <code>python3 check_csv_charset.py bigdata/ --fast -j 8 --summary-only</code>
                  </div>
                  <div className="bg-muted p-2 rounded">
                    <code># Preview conversion without changes</code><br/>
                    <code>python3 check_csv_charset.py files/ --convert-to utf-8 --dry-run</code>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Features */}
          <Card>
            <CardHeader>
              <CardTitle>Features</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <div className="space-y-2">
                  <h4 className="font-medium">🔍 Detection</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• UTF-8, UTF-16, UTF-32</li>
                    <li>• ISO-8859-* variants</li>
                    <li>• Windows-125x encodings</li>
                    <li>• ASCII detection</li>
                  </ul>
                </div>
                <div className="space-y-2">
                  <h4 className="font-medium">🔄 Conversion</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• Automatic backups</li>
                    <li>• Dry-run preview</li>
                    <li>• Rollback support</li>
                    <li>• Batch processing</li>
                  </ul>
                </div>
                <div className="space-y-2">
                  <h4 className="font-medium">⚡ Performance</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• Parallel processing</li>
                    <li>• Progress tracking</li>
                    <li>• Smart sampling</li>
                    <li>• Fast mode option</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Back to Demo */}
          <div className="text-center">
            <Button variant="outline" onClick={() => window.location.href = '/'}>
              ← Back to Demo
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}