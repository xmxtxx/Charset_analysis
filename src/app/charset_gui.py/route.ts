import { NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import { join } from 'path'

export async function GET() {
  try {
    const scriptPath = join(process.cwd(), 'charset_web_gui.py')
    const content = await readFile(scriptPath, 'utf-8')
    
    return new NextResponse(content, {
      status: 200,
      headers: {
        'Content-Type': 'text/x-python',
        'Content-Disposition': 'attachment; filename="charset_web_gui.py"',
      },
    })
  } catch {
    return NextResponse.json({ error: 'GUI script not found' }, { status: 404 })
  }
}