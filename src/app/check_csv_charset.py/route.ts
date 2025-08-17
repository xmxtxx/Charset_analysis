import { NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import { join } from 'path'

export async function GET() {
  try {
    const scriptPath = join(process.cwd(), 'check_csv_charset.py')
    const content = await readFile(scriptPath, 'utf-8')
    
    return new NextResponse(content, {
      status: 200,
      headers: {
        'Content-Type': 'text/x-python',
        'Content-Disposition': 'attachment; filename="check_csv_charset.py"',
      },
    })
  } catch {
    return NextResponse.json({ error: 'Script not found' }, { status: 404 })
  }
}