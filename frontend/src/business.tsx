import { useEffect, useMemo, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

import ArchitectureView from './ArchitectureView'
import TestDataView from './TestDataView'
import type { UserResponse } from './lib/auth'

type BusinessProps = {
  user: UserResponse | null
}

type ComplianceResult = {
  rule_id: string
  category: string
  description: string
  status: 'PASS' | 'FAIL' | 'WARNING'
  required: string
  actual: string
  element: string
  reasoning: string
  corrective_action: string
}

type RunFullResponse = {
  default_files: { dxf: string; ifc: string }
  parsed: {
    dxf: any
    ifc: any
    merged: any
  }
  compliance: {
    summary: { total: number; fail: number; pass: number; warning: number }
    results: ComplianceResult[]
  }
}

const API_URL = (import.meta.env.VITE_API_URL as string) || ''

function Business(_props: BusinessProps) {
  const [loadingDemo, setLoadingDemo] = useState(true)
  const [demo, setDemo] = useState<RunFullResponse | null>(null)
  const [svg, setSvg] = useState<string>('')
  const [error, setError] = useState<string>('')

  const [uploading, setUploading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadParsed, setUploadParsed] = useState<any | null>(null)
  const [uploadCompliance, setUploadCompliance] = useState<any | null>(null)

  const merged = demo?.parsed?.merged
  const derived = merged?.derived || {}

  const violations = useMemo(() => {
    const results = demo?.compliance?.results || []
    return results.filter((r) => r.status === 'FAIL')
  }, [demo])

  const runFullDemo = async () => {
    setError('')
    setLoadingDemo(true)
    try {
      const res = await fetch(`${API_URL}/api/demo/run-full`)
      if (!res.ok) {
        throw new Error(await res.text())
      }
      const json = (await res.json()) as RunFullResponse
      setDemo(json)

      const svgRes = await fetch(`${API_URL}/api/geometry/svg`)
      if (svgRes.ok) {
        setSvg(await svgRes.text())
      } else {
        setSvg('')
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to run demo')
    } finally {
      setLoadingDemo(false)
    }
  }

  useEffect(() => {
    void runFullDemo()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const uploadAndCheck = async () => {
    if (!uploadedFile) return

    setUploading(true)
    setUploadParsed(null)
    setUploadCompliance(null)
    setError('')

    try {
      const fd = new FormData()
      fd.append('file', uploadedFile)
      const parseRes = await fetch(`${API_URL}/api/parse`, { method: 'POST', body: fd })
      if (!parseRes.ok) throw new Error(await parseRes.text())
      const parsedJson = await parseRes.json()
      const parsed = parsedJson.parsed
      setUploadParsed(parsed)

      const checkRes = await fetch(`${API_URL}/api/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parsed_data: parsed }),
      })
      if (!checkRes.ok) throw new Error(await checkRes.text())
      const checkJson = await checkRes.json()
      setUploadCompliance(checkJson)
    } catch (e: any) {
      setError(e?.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className='mx-auto w-full max-w-7xl px-4 py-6 md:px-6'>
      <div className='mb-6 rounded-2xl bg-white/70 p-6 shadow-sm ring-1 ring-slate-200 backdrop-blur'>
        <div className='flex flex-col gap-3 md:flex-row md:items-center md:justify-between'>
          <div>
            <div className='flex flex-wrap items-center gap-2'>
              <h2 className='text-xl font-semibold text-slate-900'>Plans & Compliance CoPilot — Real Engine Demo</h2>
              <Badge className='bg-emerald-700 text-white hover:bg-emerald-700'>LIVE — Real Code, Real Data</Badge>
            </div>
            <p className='mt-1 text-sm text-slate-600'>
              Powered by <span className='font-medium text-slate-900'>IfcOpenShell</span> +{' '}
              <span className='font-medium text-slate-900'>ezdxf</span> +{' '}
              <span className='font-medium text-slate-900'>pdfplumber</span> (real open-source parsing)
            </p>
          </div>
          <div className='flex items-center gap-2'>
            <Badge variant='outline' className='border-slate-200 text-slate-700'>
              API: {API_URL || '(not set)'}
            </Badge>
          </div>
        </div>
      </div>

      <Tabs defaultValue='demo' className='w-full'>
        <TabsList className='mb-6'>
          <TabsTrigger value='demo'>▶ Live Demo</TabsTrigger>
          <TabsTrigger value='docs'>📐 Architecture &amp; Open-Source</TabsTrigger>
          <TabsTrigger value='data'>🗂 Test Data</TabsTrigger>
        </TabsList>

        <TabsContent value='demo'>
      {error ? (
        <Card className='mb-6 border-red-200 bg-red-50'>
          <CardHeader>
            <CardTitle className='text-red-900'>Error</CardTitle>
            <CardDescription className='text-red-700'>{error}</CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      <div className='grid gap-6 lg:grid-cols-2'>
        <Card className='overflow-hidden'>
          <CardHeader>
            <CardTitle>Quick Demo Panel</CardTitle>
            <CardDescription>One-click: parse villa DXF + (optional) IFC, then check all compliance rules.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className='flex flex-col gap-3'>
              <Button
                size='lg'
                className='bg-emerald-700 text-white hover:bg-emerald-800'
                onClick={() => void runFullDemo()}
                disabled={loadingDemo}
              >
                ▶ Run Full Demo (Villa Riyadh)
              </Button>

              {loadingDemo ? (
                <div className='grid gap-2'>
                  <Skeleton className='h-5 w-2/3' />
                  <Skeleton className='h-5 w-1/2' />
                </div>
              ) : demo ? (
                <div className='rounded-lg bg-slate-50 p-4 ring-1 ring-slate-200'>
                  <div className='flex flex-wrap items-center justify-between gap-2'>
                    <div className='text-sm text-slate-700'>
                      <span className='font-medium text-slate-900'>Summary:</span> {demo.compliance.summary.fail} FAIL /{' '}
                      {demo.compliance.summary.pass} PASS / {demo.compliance.summary.warning} WARNING
                    </div>
                    <Badge
                      className={
                        demo.compliance.summary.fail > 0
                          ? 'bg-red-600 text-white hover:bg-red-600'
                          : 'bg-emerald-700 text-white hover:bg-emerald-700'
                      }
                    >
                      {demo.compliance.summary.fail > 0 ? 'NON-COMPLIANT' : 'COMPLIANT'}
                    </Badge>
                  </div>
                  <div className='mt-3 text-sm text-slate-700'>
                    Expected demo: <span className='font-medium text-slate-900'>5 violations</span> (front setback, bedroom 2, bathroom 2, corridor width, interior doors).
                  </div>
                </div>
              ) : null}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Upload Panel</CardTitle>
            <CardDescription>Upload an IFC / DXF / PDF, then parse → check.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className='flex flex-col gap-3'>
              <Input
                type='file'
                accept='.ifc,.dxf,.pdf'
                onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
              />
              <div className='flex items-center gap-2'>
                <Button
                  onClick={() => void uploadAndCheck()}
                  disabled={!uploadedFile || uploading}
                  className='bg-slate-900 text-white hover:bg-slate-800'
                >
                  {uploading ? 'Parsing…' : 'Parse & Check'}
                </Button>
                {uploadedFile ? <span className='text-sm text-slate-600'>{uploadedFile.name}</span> : null}
              </div>

              {uploadParsed ? (
                <div className='rounded-lg bg-slate-50 p-3 text-sm text-slate-700 ring-1 ring-slate-200'>
                  Parsed source: <span className='font-medium text-slate-900'>{uploadParsed.source}</span>
                </div>
              ) : null}

              {uploadCompliance ? (
                <div className='rounded-lg bg-slate-50 p-3 text-sm text-slate-700 ring-1 ring-slate-200'>
                  Summary: {uploadCompliance.summary.fail} FAIL / {uploadCompliance.summary.pass} PASS /{' '}
                  {uploadCompliance.summary.warning} WARNING
                </div>
              ) : null}
            </div>
          </CardContent>
        </Card>
      </div>

      <Separator className='my-6' />

      <Card className='mb-6'>
        <CardHeader>
          <CardTitle>Parsing Results (Extracted Data)</CardTitle>
          <CardDescription>Key measurements extracted from the real DXF/IFC parsing.</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingDemo ? (
            <div className='grid gap-3'>
              <Skeleton className='h-6 w-full' />
              <Skeleton className='h-6 w-2/3' />
              <Skeleton className='h-40 w-full' />
            </div>
          ) : demo ? (
            <div className='grid gap-6 md:grid-cols-2'>
              <div className='rounded-xl bg-slate-50 p-4 ring-1 ring-slate-200'>
                <div className='text-sm font-semibold text-slate-900'>Setbacks / Building</div>
                <div className='mt-3 grid gap-2 text-sm text-slate-700'>
                  <div className='flex items-center justify-between gap-3'>
                    <span>Front setback</span>
                    <span className='font-medium text-slate-900'>{derived.front_setback?.toFixed?.(2)} m</span>
                  </div>
                  <div className='flex items-center justify-between gap-3'>
                    <span>Side setback (min)</span>
                    <span className='font-medium text-slate-900'>{derived.side_setback_min?.toFixed?.(2)} m</span>
                  </div>
                  <div className='flex items-center justify-between gap-3'>
                    <span>Rear setback</span>
                    <span className='font-medium text-slate-900'>{derived.rear_setback?.toFixed?.(2)} m</span>
                  </div>
                  <div className='flex items-center justify-between gap-3'>
                    <span>Building height</span>
                    <span className='font-medium text-slate-900'>{derived.building_height?.toFixed?.(2)} m</span>
                  </div>
                  <div className='flex items-center justify-between gap-3'>
                    <span>Lot coverage</span>
                    <span className='font-medium text-slate-900'>{derived.lot_coverage_pct?.toFixed?.(1)}%</span>
                  </div>
                  <div className='flex items-center justify-between gap-3'>
                    <span>Corridor width</span>
                    <span className='font-medium text-slate-900'>{derived.corridor_width?.toFixed?.(2)} m</span>
                  </div>
                </div>
              </div>

              <div className='rounded-xl bg-slate-50 p-4 ring-1 ring-slate-200'>
                <div className='text-sm font-semibold text-slate-900'>Rooms (from DXF room polygons / IFC quantities)</div>
                <div className='mt-3 overflow-hidden rounded-lg ring-1 ring-slate-200'>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead className='text-right'>Area (m²)</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(merged?.rooms || []).map((r: any) => (
                        <TableRow key={r.name}>
                          <TableCell className='font-medium text-slate-900'>{r.name}</TableCell>
                          <TableCell className='text-slate-700'>{r.category}</TableCell>
                          <TableCell className='text-right text-slate-700'>{Number(r.area).toFixed(2)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card className='mb-6'>
        <CardHeader>
          <CardTitle>Compliance Results</CardTitle>
          <CardDescription>
            Table is color-coded (green PASS / red FAIL). Click a row to expand reasoning & corrective action.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingDemo ? (
            <div className='grid gap-3'>
              <Skeleton className='h-10 w-full' />
              <Skeleton className='h-10 w-full' />
              <Skeleton className='h-10 w-full' />
            </div>
          ) : demo ? (
            <div className='rounded-xl ring-1 ring-slate-200'>
              <div className='grid grid-cols-12 gap-2 bg-slate-50 px-4 py-3 text-xs font-semibold text-slate-700'>
                <div className='col-span-2'>Rule ID</div>
                <div className='col-span-2'>Category</div>
                <div className='col-span-3'>Description</div>
                <div className='col-span-2'>Required</div>
                <div className='col-span-2'>Actual</div>
                <div className='col-span-1 text-right'>Status</div>
              </div>

              <Accordion type='single' collapsible className='w-full'>
                {demo.compliance.results.map((r) => {
                  const rowBg =
                    r.status === 'PASS'
                      ? 'bg-emerald-50'
                      : r.status === 'FAIL'
                        ? 'bg-red-50'
                        : 'bg-amber-50'

                  const badgeCls =
                    r.status === 'PASS'
                      ? 'bg-emerald-700 text-white hover:bg-emerald-700'
                      : r.status === 'FAIL'
                        ? 'bg-red-600 text-white hover:bg-red-600'
                        : 'bg-amber-600 text-white hover:bg-amber-600'

                  return (
                    <AccordionItem key={r.rule_id} value={r.rule_id} className='border-0'>
                      <AccordionTrigger className={`px-4 py-3 no-underline hover:no-underline ${rowBg}`}>
                        <div className='grid w-full grid-cols-12 gap-2 text-left text-sm'>
                          <div className='col-span-2 font-semibold text-slate-900'>{r.rule_id}</div>
                          <div className='col-span-2 text-slate-700'>{r.category}</div>
                          <div className='col-span-3 text-slate-700'>{r.description}</div>
                          <div className='col-span-2 text-slate-700'>{r.required}</div>
                          <div className='col-span-2 text-slate-700'>{r.actual}</div>
                          <div className='col-span-1 flex justify-end'>
                            <Badge className={badgeCls}>{r.status}</Badge>
                          </div>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className='px-4 pb-4 pt-2'>
                        <div className='grid gap-3 text-sm text-slate-700 md:grid-cols-2'>
                          <div>
                            <div className='text-xs font-semibold text-slate-900'>Element</div>
                            <div className='mt-1'>{r.element}</div>
                          </div>
                          <div>
                            <div className='text-xs font-semibold text-slate-900'>Corrective Action</div>
                            <div className='mt-1'>{r.corrective_action}</div>
                          </div>
                          <div className='md:col-span-2'>
                            <div className='text-xs font-semibold text-slate-900'>Reasoning</div>
                            <div className='mt-1 whitespace-pre-wrap'>{r.reasoning}</div>
                          </div>
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  )
                })}
              </Accordion>
            </div>
          ) : null}

          {!loadingDemo && demo ? (
            <div className='mt-4 text-sm text-slate-700'>
              Violations detected ({violations.length}):{' '}
              <span className='font-medium text-slate-900'>
                {violations.map((v) => v.rule_id).join(', ')}
              </span>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card className='mb-6'>
        <CardHeader>
          <CardTitle>Floor Plan Overlay (DXF → SVG)</CardTitle>
          <CardDescription>Rendered inline. Violations are highlighted in red. Hover a room to see its name + area.</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingDemo ? (
            <Skeleton className='h-80 w-full' />
          ) : svg ? (
            <div className='overflow-hidden rounded-xl bg-white ring-1 ring-slate-200'>
              <div className='p-3' dangerouslySetInnerHTML={{ __html: svg }} />
            </div>
          ) : (
            <div className='rounded-lg bg-slate-50 p-4 text-sm text-slate-700 ring-1 ring-slate-200'>
              SVG not available.
            </div>
          )}
        </CardContent>
      </Card>

      <footer className='rounded-2xl bg-white/70 p-6 text-sm text-slate-700 shadow-sm ring-1 ring-slate-200 backdrop-blur'>
        <div className='font-semibold text-slate-900'>Tech Stack</div>
        <div className='mt-2 grid gap-1'>
          <a className='underline underline-offset-4 hover:text-slate-900' href='https://github.com/IfcOpenShell/IfcOpenShell' target='_blank' rel='noreferrer'>
            IfcOpenShell — https://github.com/IfcOpenShell/IfcOpenShell
          </a>
          <a className='underline underline-offset-4 hover:text-slate-900' href='https://github.com/mozman/ezdxf' target='_blank' rel='noreferrer'>
            ezdxf — https://github.com/mozman/ezdxf
          </a>
          <a className='underline underline-offset-4 hover:text-slate-900' href='https://github.com/jsvine/pdfplumber' target='_blank' rel='noreferrer'>
            pdfplumber — https://github.com/jsvine/pdfplumber
          </a>
        </div>
        <div className='mt-3 text-slate-600'>
          All parsing is performed by these real open-source libraries. No simulation or mockup.
        </div>
      </footer>
        </TabsContent>

        <TabsContent value='docs'>
          <ArchitectureView />
        </TabsContent>

        <TabsContent value='data'>
          <TestDataView />
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default Business
