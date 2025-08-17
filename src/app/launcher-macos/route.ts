import { NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import { join } from 'path'

export async function GET() {
  try {
    const scriptPath = join(process.cwd(), 'run_charset_analyzer.command')
    const content = await readFile(scriptPath, 'utf-8')
    
    return new NextResponse(content, {
      status: 200,
      headers: {
        'Content-Type': 'application/x-sh',
        'Content-Disposition': 'attachment; filename="run_charset_analyzer.command"',
      },
    })
  } catch {
    return NextResponse.json({ error: 'macOS launcher not found' }, { status: 404 })
  }
}