import { useEffect, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'

const API_URL = (import.meta.env.VITE_API_URL as string) || ''

type TestFile = {
  name: string
  size: number
  type: string
  kind: string
  description: string
  parsed_by: string
  download_url: string
  preview_url: string
}

type PreviewData = {
  name: string
  content: string
  total_lines: number
  truncated: boolean
}

function humanSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

const TYPE_COLOR: Record<string, string> = {
  DXF: 'bg-blue-100 text-blue-800',
  IFC: 'bg-emerald-100 text-emerald-800',
  PDF: 'bg-amber-100 text-amber-800',
}

function TestDataView() {
  const [loading, setLoading] = useState(true)
  const [files, setFiles] = useState<TestFile[]>([])
  const [error, setError] = useState('')

  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [preview, setPreview] = useState<PreviewData | null>(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const res = await fetch(`${API_URL}/api/test-data`)
        if (!res.ok) throw new Error(await res.text())
        const json = await res.json()
        setFiles(json.files || [])
      } catch (e: any) {
        setError(e?.message || 'Failed to load test data')
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [])

  const openPreview = async (f: TestFile) => {
    setPreviewOpen(true)
    setPreviewLoading(true)
    setPreview(null)
    try {
      const res = await fetch(`${API_URL}${f.preview_url}`)
      if (!res.ok) throw new Error(await res.text())
      setPreview((await res.json()) as PreviewData)
    } catch (e: any) {
      setPreview({ name: f.name, content: `Failed to load preview: ${e?.message || e}`, total_lines: 0, truncated: false })
    } finally {
      setPreviewLoading(false)
    }
  }

  return (
    <div className='grid gap-6'>
      <Card>
        <CardHeader>
          <CardTitle>Real Test Data</CardTitle>
          <CardDescription>
            The exact villa files parsed by the live engine (Riyadh, Plot&nbsp;1042). Preview the raw content in the
            browser, or download to open in your own CAD / BIM / PDF tools.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className='rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700'>{error}</div>
          ) : loading ? (
            <div className='grid gap-3'>
              <Skeleton className='h-24 w-full' />
              <Skeleton className='h-24 w-full' />
              <Skeleton className='h-24 w-full' />
            </div>
          ) : (
            <div className='grid gap-4 md:grid-cols-3'>
              {files.map((f) => (
                <div key={f.name} className='flex flex-col rounded-xl bg-slate-50 p-4 ring-1 ring-slate-200'>
                  <div className='flex items-center justify-between gap-2'>
                    <Badge className={`${TYPE_COLOR[f.type] || 'bg-slate-200 text-slate-800'} hover:opacity-100`}>
                      {f.type}
                    </Badge>
                    <span className='text-xs text-slate-500'>{humanSize(f.size)}</span>
                  </div>
                  <div className='mt-2 break-all text-sm font-semibold text-slate-900'>{f.name}</div>
                  <div className='mt-1 text-xs text-slate-600'>{f.kind}</div>
                  <p className='mt-2 flex-1 text-xs leading-relaxed text-slate-600'>{f.description}</p>
                  {f.parsed_by ? (
                    <div className='mt-2 text-xs text-slate-500'>
                      Parsed by <span className='font-medium text-slate-700'>{f.parsed_by}</span>
                    </div>
                  ) : null}
                  <div className='mt-3 flex items-center gap-2'>
                    <Button
                      size='sm'
                      variant='outline'
                      className='border-slate-300'
                      onClick={() => void openPreview(f)}
                    >
                      👁 Preview
                    </Button>
                    <a href={`${API_URL}${f.download_url}`} download>
                      <Button size='sm' className='bg-emerald-700 text-white hover:bg-emerald-800'>
                        ⬇ Download
                      </Button>
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className='max-w-3xl'>
          <DialogHeader>
            <DialogTitle>Preview — {preview?.name || '…'}</DialogTitle>
            <DialogDescription>
              {preview
                ? `${preview.total_lines} lines${preview.truncated ? ' · showing the first part only (download for the full file)' : ''}`
                : 'Loading…'}
            </DialogDescription>
          </DialogHeader>
          {previewLoading ? (
            <div className='grid gap-2'>
              <Skeleton className='h-5 w-full' />
              <Skeleton className='h-5 w-5/6' />
              <Skeleton className='h-64 w-full' />
            </div>
          ) : (
            <pre className='max-h-[60vh] overflow-auto rounded-lg bg-slate-900 p-4 text-xs leading-relaxed text-slate-100'>
              {preview?.content}
            </pre>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default TestDataView
