import { NextResponse } from 'next/server'

export async function POST() {
  try {
    // For Vercel deployment, use mock demo data since Python isn't available
    // This simulates the actual analysis output from the Python script
    
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    const mockOutput = `============================================================
CSV Character Encoding Detection
============================================================
📁 Top directory: /samples
🔎 Structure: Subfolder mode - **/*.csv (recursive search)
────────────────────────────────────────────────────────────

Scanning folders...
Found 3 CSV files in 1 folders

Processing CSV files: [██████████████████████████████████████████████████] 3/3 (100.0%)

────────────────────────────────────────────────────────────
Results by Folder:

Encoding Distribution samples:
  ISO-8859-1: 1 files (33.3%)
  ascii: 1 files (33.3%)
  utf-8: 1 files (33.3%)


══════════════════════════════════════════════════
OVERALL SUMMARY
══════════════════════════════════════════════════
Total folders analyzed: 1
Total CSV files processed: 3
Successfully detected: 3
Detection success rate: 100.0%
Total runtime: 0s

Overall Encoding Distribution:
  ISO-8859-1: 1 files (33.3%)
  ascii: 1 files (33.3%)
  utf-8: 1 files (33.3%)

✅ Analysis complete!`
    
    return NextResponse.json({ 
      success: true,
      output: mockOutput,
      filesProcessed: 3
    })

  } catch (error) {
    console.error('Demo error:', error)
    return NextResponse.json({ 
      error: 'Demo execution failed', 
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}