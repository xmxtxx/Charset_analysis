import { NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import { join } from 'path'

export async function GET() {
  try {
    const scriptPath = join(process.cwd(), 'run_charset_analyzer.bat')
    const content = await readFile(scriptPath, 'utf-8')
    
    return new NextResponse(content, {
      status: 200,
      headers: {
        'Content-Type': 'application/x-bat',
        'Content-Disposition': 'attachment; filename="run_charset_analyzer.bat"',
      },
    })
  } catch {
    return NextResponse.json({ error: 'Windows launcher not found' }, { status: 404 })
  }
}