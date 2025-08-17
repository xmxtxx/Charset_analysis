"use client"

import { Header } from "@/components/header"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, Terminal, Shield, Copy, Check, X, AlertTriangle } from "lucide-react"
import { useState } from "react"

export default function DownloadPage() {
  const [copied, setCopied] = useState<string | null>(null)
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(false)
  const [showDisclaimerModal, setShowDisclaimerModal] = useState(false)
  const [pendingDownload, setPendingDownload] = useState<{href: string, filename: string} | null>(null)

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopied(id)
    setTimeout(() => setCopied(null), 2000)
  }

  const handleDownloadClick = (e: React.MouseEvent, href: string, filename: string) => {
    e.preventDefault()
    
    if (disclaimerAccepted) {
      // Proceed with download
      triggerDownload(href, filename)
    } else {
      // Show disclaimer modal
      setPendingDownload({href, filename})
      setShowDisclaimerModal(true)
    }
  }

  const triggerDownload = (href: string, filename: string) => {
    const link = document.createElement('a')
    link.href = href
    link.download = filename
    link.click()
  }

  const acceptDisclaimer = () => {
    setDisclaimerAccepted(true)
    setShowDisclaimerModal(false)
    
    // Trigger the pending download
    if (pendingDownload) {
      triggerDownload(pendingDownload.href, pendingDownload.filename)
      setPendingDownload(null)
    }
  }

  const closeDisclaimer = () => {
    setShowDisclaimerModal(false)
    setPendingDownload(null)
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

          {/* Download Options by Platform */}
          <Card className="border-2 border-primary/20 mb-6">
            <CardHeader className="text-center">
              <CardTitle className="flex items-center justify-center gap-2 text-2xl">
                <Download className="h-6 w-6" />
                Easy Mode: Double-Click Launchers
              </CardTitle>
              <CardDescription className="text-lg">
                True double-click experience - downloads everything you need!
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3 mb-6">
                <a 
                  href="/launcher-macos" 
                  download="run_charset_analyzer.command"
                  onClick={(e) => handleDownloadClick(e, "/launcher-macos", "run_charset_analyzer.command")}
                  className="block text-center p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer text-decoration-none"
                  style={{textDecoration: 'none'}}
                >
                  <div className="text-4xl mb-2 pointer-events-none">🍎</div>
                  <h3 className="font-semibold mb-2 pointer-events-none">macOS</h3>
                  <div className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 w-full pointer-events-none">
                    Download .command
                  </div>
                </a>
                
                <a 
                  href="/launcher-windows" 
                  download="run_charset_analyzer.bat"
                  onClick={(e) => handleDownloadClick(e, "/launcher-windows", "run_charset_analyzer.bat")}
                  className="block text-center p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer text-decoration-none"
                  style={{textDecoration: 'none'}}
                >
                  <div className="text-4xl mb-2 pointer-events-none">🪟</div>
                  <h3 className="font-semibold mb-2 pointer-events-none">Windows</h3>
                  <div className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 w-full pointer-events-none">
                    Download .bat
                  </div>
                </a>
                
                <a 
                  href="/launcher-linux" 
                  download="run_charset_analyzer.sh"
                  onClick={(e) => handleDownloadClick(e, "/launcher-linux", "run_charset_analyzer.sh")}
                  className="block text-center p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer text-decoration-none"
                  style={{textDecoration: 'none'}}
                >
                  <div className="text-4xl mb-2 pointer-events-none">🐧</div>
                  <h3 className="font-semibold mb-2 pointer-events-none">Linux</h3>
                  <div className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 w-full pointer-events-none">
                    Download .sh
                  </div>
                </a>
              </div>
              
              <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
                <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">📦 Complete Package Included:</h4>
                <div className="grid gap-2 md:grid-cols-2 text-sm text-blue-800 dark:text-blue-200">
                  <div>• ✅ Web interface (charset_web_gui.py)</div>
                  <div>• ✅ Analysis engine (check_csv_charset.py)</div>
                  <div>• ✅ Double-click launcher</div>
                  <div>• ✅ Auto-dependency installation</div>
                </div>
              </div>
              
              <div className="bg-yellow-50 dark:bg-yellow-950 p-4 rounded-lg border border-yellow-200 dark:border-yellow-800">
                <div className="flex items-start gap-3">
                  <div className="text-yellow-600 dark:text-yellow-400 text-xl">⚠️</div>
                  <div>
                    <h4 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-1">Security Notice</h4>
                    <p className="text-sm text-yellow-700 dark:text-yellow-300">
                      Executable files may trigger security warnings. See full disclaimer below for platform-specific instructions.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Advanced Options */}
          <Card className="border-2 border-secondary/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Terminal className="h-5 w-5" />
                Advanced: Individual Files
              </CardTitle>
              <CardDescription>
                For developers who want individual components
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-medium mb-2">Web Interface</h4>
                  <a 
                    href="/charset_gui.py" 
                    download="charset_web_gui.py"
                    onClick={(e) => handleDownloadClick(e, "/charset_gui.py", "charset_web_gui.py")}
                    className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2 w-full text-decoration-none"
                    style={{textDecoration: 'none'}}
                  >
                    <Download className="mr-2 h-4 w-4 pointer-events-none" />
                    <span className="pointer-events-none">charset_web_gui.py</span>
                  </a>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Analysis Engine</h4>
                  <a 
                    href="/check_csv_charset.py" 
                    download="check_csv_charset.py"
                    onClick={(e) => handleDownloadClick(e, "/check_csv_charset.py", "check_csv_charset.py")}
                    className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2 w-full text-decoration-none"
                    style={{textDecoration: 'none'}}
                  >
                    <Download className="mr-2 h-4 w-4 pointer-events-none" />
                    <span className="pointer-events-none">check_csv_charset.py</span>
                  </a>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Installation Guide */}
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Download className="h-5 w-5" />
                  GUI Setup (Recommended)
                </CardTitle>
                <CardDescription>
                  Easy setup for the graphical interface
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
                  <h4 className="font-medium mb-2">2. Run Web Interface</h4>
                  <div className="bg-muted p-3 rounded-lg flex items-center justify-between">
                    <code className="text-sm">python3 charset_web_gui.py</code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard("python3 charset_web_gui.py", 'gui')}
                    >
                      {copied === 'gui' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    💡 Make sure both files are in the same folder, then double-click or run the command
                  </p>
                  <p className="text-xs text-muted-foreground">
                    🌐 Browser will open automatically with the interface
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Terminal className="h-5 w-5" />
                  Command Line Setup
                </CardTitle>
                <CardDescription>
                  Setup for advanced users and automation
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">1. Install Dependencies</h4>
                  <div className="bg-muted p-3 rounded-lg flex items-center justify-between">
                    <code className="text-sm">{installCommand}</code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(installCommand, 'install2')}
                    >
                      {copied === 'install2' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">2. Make Executable (Optional)</h4>
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

          {/* Security & Legal Disclaimers */}
          <Card className="border-2 border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-950">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-yellow-800 dark:text-yellow-200">
                <Shield className="h-5 w-5" />
                ⚠️ Important Security & Legal Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-white dark:bg-gray-900 p-4 rounded-lg border border-yellow-200 dark:border-yellow-700">
                <h4 className="font-semibold text-red-700 dark:text-red-400 mb-3">🚨 Security Warnings for Executable Files</h4>
                <div className="space-y-3 text-sm">
                  <div className="bg-red-50 dark:bg-red-950 p-3 rounded border-l-4 border-red-400">
                    <p className="font-medium text-red-800 dark:text-red-300">Antivirus & Security Software:</p>
                    <p className="text-red-700 dark:text-red-400">Your antivirus or security software may flag the launcher files (.bat, .command, .sh) as potentially dangerous because they are executable scripts. This is normal security behavior.</p>
                  </div>
                  
                  <div className="space-y-2">
                    <h5 className="font-medium text-gray-800 dark:text-gray-200">Platform-Specific Security Steps:</h5>
                    
                    <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded">
                      <p className="font-medium text-blue-700 dark:text-blue-400">🍎 macOS:</p>
                      <ul className="list-disc ml-5 space-y-1 text-gray-700 dark:text-gray-300">
                        <li>Right-click the .command file → "Open" (don't double-click first time)</li>
                        <li>Click "Open" when prompted about unidentified developer</li>
                        <li>May need: System Preferences → Security & Privacy → Allow anyway</li>
                        <li>Terminal permissions may be required</li>
                      </ul>
                    </div>
                    
                    <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded">
                      <p className="font-medium text-green-700 dark:text-green-400">🪟 Windows:</p>
                      <ul className="list-disc ml-5 space-y-1 text-gray-700 dark:text-gray-300">
                        <li>Windows Defender may block execution initially</li>
                        <li>Click "More info" → "Run anyway" if SmartScreen appears</li>
                        <li>Add to Windows Defender exclusions if needed</li>
                        <li>UAC prompt may appear - click "Yes" to allow</li>
                      </ul>
                    </div>
                    
                    <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded">
                      <p className="font-medium text-purple-700 dark:text-purple-400">🐧 Linux:</p>
                      <ul className="list-disc ml-5 space-y-1 text-gray-700 dark:text-gray-300">
                        <li>Make executable: <code className="bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">chmod +x run_charset_analyzer.sh</code></li>
                        <li>Run from terminal or double-click if file manager supports it</li>
                        <li>Some distributions may require manual execution permission</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-900 p-4 rounded-lg border border-yellow-200 dark:border-yellow-700">
                <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">📋 Legal Disclaimer</h4>
                <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                  <p className="font-medium">NO WARRANTY OR LIABILITY:</p>
                  <ul className="list-disc ml-5 space-y-1">
                    <li>This software is provided "AS IS" without warranty of any kind</li>
                    <li>No liability is accepted for any damage, data loss, or security issues</li>
                    <li>Use at your own risk and responsibility</li>
                    <li>Always backup your data before running any conversion operations</li>
                    <li>Test on sample data first before processing important files</li>
                  </ul>
                  
                  <p className="font-medium mt-3">SECURITY RESPONSIBILITY:</p>
                  <ul className="list-disc ml-5 space-y-1">
                    <li>You are responsible for verifying the safety of downloaded files</li>
                    <li>Review the source code if you have security concerns</li>
                    <li>Configure your security software appropriately</li>
                    <li>Understand the risks of running executable scripts</li>
                  </ul>
                </div>
              </div>

              <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg border border-blue-200 dark:border-blue-700">
                <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">✅ Why These Warnings Exist</h4>
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  These launcher files are legitimate scripts that automatically install dependencies and start the tool. 
                  Security software flags them because executable scripts can be misused by malicious software. 
                  Our launchers only install Python packages and run the charset analyzer - you can review the code yourself.
                </p>
              </div>

              <div className="bg-green-50 dark:bg-green-950 p-4 rounded-lg border border-green-200 dark:border-green-700">
                <h4 className="font-semibold text-green-800 dark:text-green-200 mb-2">🔍 Alternative: Manual Installation</h4>
                <p className="text-sm text-green-700 dark:text-green-300">
                  If you prefer not to use the launcher files, you can download the individual Python files and run them manually. 
                  This avoids all executable security warnings but requires manual dependency installation.
                </p>
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

      {/* Disclaimer Modal */}
      {showDisclaimerModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="h-6 w-6 text-yellow-500" />
                  <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                    Disclaimer & Terms of Use
                  </h2>
                </div>
                <button
                  onClick={closeDisclaimer}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4 text-sm text-gray-700 dark:text-gray-300">
                <div className="bg-red-50 dark:bg-red-950 p-4 rounded-lg border border-red-200 dark:border-red-800">
                  <h3 className="font-semibold text-red-800 dark:text-red-300 mb-2">⚠️ Important Legal Notice</h3>
                  <p className="text-red-700 dark:text-red-400">
                    By downloading and using this software, you acknowledge and agree to the following terms:
                  </p>
                </div>

                <div className="space-y-3">
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100">NO WARRANTY OR LIABILITY</h4>
                    <ul className="list-disc ml-5 space-y-1">
                      <li>This software is provided "AS IS" without warranty of any kind</li>
                      <li>No liability is accepted for any damage, data loss, or security issues</li>
                      <li>Use at your own risk and responsibility</li>
                      <li>Always backup your data before running any operations</li>
                      <li>Test on sample data first before processing important files</li>
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100">SECURITY RESPONSIBILITY</h4>
                    <ul className="list-disc ml-5 space-y-1">
                      <li>You are responsible for verifying the safety of downloaded files</li>
                      <li>Your security software may flag executable files - this is normal</li>
                      <li>Review the source code if you have security concerns</li>
                      <li>Configure your security software appropriately</li>
                      <li>Understand the risks of running executable scripts</li>
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100">PLATFORM SECURITY WARNINGS</h4>
                    <ul className="list-disc ml-5 space-y-1">
                      <li><strong>macOS:</strong> May require right-click → Open for first-time execution</li>
                      <li><strong>Windows:</strong> May trigger SmartScreen or antivirus warnings</li>
                      <li><strong>Linux:</strong> May require chmod +x to make files executable</li>
                    </ul>
                  </div>
                </div>

                <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg border border-blue-200 dark:border-blue-700">
                  <p className="text-blue-800 dark:text-blue-300">
                    <strong>Swiss Data Protection Compliance:</strong> This tool processes all data locally on your machine. 
                    No data is transmitted to external servers. Your CSV files never leave your computer.
                  </p>
                </div>
              </div>

              <div className="flex gap-3 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                <Button 
                  variant="outline" 
                  onClick={closeDisclaimer}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={acceptDisclaimer}
                  className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  I Accept & Download
                </Button>
              </div>

              <p className="text-xs text-gray-500 dark:text-gray-400 mt-3 text-center">
                By clicking "I Accept & Download", you confirm that you have read, understood, and agree to these terms.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}