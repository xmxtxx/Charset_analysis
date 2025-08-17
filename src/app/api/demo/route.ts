import { NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'
import { join } from 'path'

const execAsync = promisify(exec)

export async function POST() {
  try {
    // Path to the public directory (which contains the samples subfolder)
    const publicDir = join(process.cwd(), 'public')
    
    // Execute Python script on the public directory
    const pythonScript = join(process.cwd(), 'check_csv_charset.py')
    const command = `python3 "${pythonScript}" "${publicDir}" --summary-only`
    
    const { stdout, stderr } = await execAsync(command)
    
    if (stderr && !stderr.includes('Warning') && !stderr.includes('ℹ')) {
      console.error('Python script error:', stderr)
      return NextResponse.json({ error: 'Demo failed', details: stderr }, { status: 500 })
    }

    // Strip ANSI color codes from output for clean display
    const cleanOutput = stdout.replace(/\x1b\[[0-9;]*m/g, '')

    // Count the number of CSV files in samples
    const { stdout: fileCount } = await execAsync(`find "${publicDir}" -name "*.csv" | wc -l`)
    
    return NextResponse.json({ 
      success: true,
      output: cleanOutput,
      filesProcessed: parseInt(fileCount.trim()) || 3
    })

  } catch (error) {
    console.error('Demo error:', error)
    return NextResponse.json({ 
      error: 'Demo execution failed', 
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}