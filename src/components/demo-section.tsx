"use client"

import { useState } from 'react'
import { Play, Download, FileText, Zap, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface DemoResult {
  success: boolean
  output: string
  filesProcessed: number
  error?: string
}

const sampleFiles = [
  { name: 'utf8_sample.csv', description: 'UTF-8 encoded file with international characters', encoding: 'UTF-8' },
  { name: 'iso_sample.csv', description: 'ISO-8859-1 encoded file with European characters', encoding: 'ISO-8859-1' },
  { name: 'ascii_sample.csv', description: 'ASCII encoded file with basic English characters', encoding: 'ASCII' }
]

export function DemoSection() {
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState<DemoResult | null>(null)

  const runDemo = async () => {
    setIsRunning(true)
    setResult(null)

    try {
      const response = await fetch('/api/demo', {
        method: 'POST',
      })
      
      const data: DemoResult = await response.json()
      setResult(data)
    } catch {
      setResult({
        success: false,
        output: '',
        filesProcessed: 0,
        error: 'Failed to run demo'
      })
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <section className="py-16 bg-muted/30">
      <div className="container mx-auto px-4">
        <div className="space-y-8">
          {/* Header */}
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-bold tracking-tighter md:text-4xl">
              Try the Demo
            </h2>
            <p className="mx-auto max-w-[600px] text-muted-foreground md:text-lg">
              See the Python charset analysis tool in action with sample CSV files. 
              Real processing, real results - all running locally.
            </p>
          </div>

          {/* Demo Cards */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Demo Runner */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Play className="h-5 w-5" />
                  Live Demo
                </CardTitle>
                <CardDescription>
                  Run the Python script on sample CSV files to see encoding detection in action
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <h4 className="font-medium">Sample Files Included:</h4>
                  {sampleFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        <span className="text-sm font-medium">{file.name}</span>
                      </div>
                      <span className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded">
                        {file.encoding}
                      </span>
                    </div>
                  ))}
                </div>

                <Button 
                  onClick={runDemo} 
                  disabled={isRunning}
                  className="w-full"
                  size="lg"
                >
                  {isRunning ? (
                    <>
                      <Zap className="mr-2 h-4 w-4 animate-pulse" />
                      Running Python Analysis...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      Run Demo Analysis
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Download Option */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Download className="h-5 w-5" />
                  Download for Real Use
                </CardTitle>
                <CardDescription>
                  Get the Python script to analyze your own CSV files locally
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-sm">
                    <Shield className="h-4 w-4 text-green-600" />
                    <span>100% local processing - your data stays private</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Zap className="h-4 w-4 text-blue-600" />
                    <span>Parallel processing for fast analysis</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <FileText className="h-4 w-4 text-purple-600" />
                    <span>Supports all major character encodings</span>
                  </div>
                </div>

                <Button 
                  variant="outline" 
                  className="w-full"
                  size="lg"
                  onClick={() => window.location.href = '/download'}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download Python Tool
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Results */}
          {result && (
            <Card>
              <CardHeader>
                <CardTitle className={result.success ? "text-green-600" : "text-red-600"}>
                  Demo Results
                </CardTitle>
                {result.success && (
                  <CardDescription>
                    Analyzed {result.filesProcessed} sample CSV files
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent>
                {result.success ? (
                  <div className="space-y-4">
                    <div className="bg-slate-950 text-gray-100 p-6 rounded-lg font-mono text-sm overflow-x-auto border">
                      <pre className="whitespace-pre-wrap leading-relaxed">{result.output}</pre>
                    </div>
                    <div className="flex justify-center">
                      <Button onClick={() => window.location.href = '/download'} size="lg">
                        <Download className="mr-2 h-4 w-4" />
                        Download Tool for Your Files
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-red-600">
                    <p className="font-medium">{result.error}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </section>
  )
}