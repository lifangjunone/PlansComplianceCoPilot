import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

/**
 * Docs / Architecture view.
 *
 * Static, self-contained documentation so the team can show — feature by
 * feature — exactly which open-source project powers each capability. No
 * backend dependency, so this tab always renders even if the API is down.
 */

type FeatureRow = {
  feature: string
  capability: string
  oss: string
  repo: string
  license: string
  file: string
}

const FEATURES: FeatureRow[] = [
  {
    feature: 'IFC / BIM model parsing',
    capability: 'Reads .ifc models; extracts storeys, spaces, quantities and building height.',
    oss: 'IfcOpenShell',
    repo: 'https://github.com/IfcOpenShell/IfcOpenShell',
    license: 'LGPL-3.0',
    file: 'backend/parser_ifc.py',
  },
  {
    feature: 'DXF / 2D CAD parsing',
    capability: 'Reads .dxf drawings; extracts plot boundary, building outline, room polygons, doors, setbacks and widths.',
    oss: 'ezdxf',
    repo: 'https://github.com/mozman/ezdxf',
    license: 'MIT',
    file: 'backend/parser_dxf.py',
  },
  {
    feature: 'PDF submission extraction',
    capability: 'Extracts text and vector line geometry from planning submission PDFs.',
    oss: 'pdfplumber',
    repo: 'https://github.com/jsvine/pdfplumber',
    license: 'MIT',
    file: 'backend/parser_pdf.py',
  },
  {
    feature: 'Compliance rule engine',
    capability: 'Deterministic checks of extracted quantities against ADG / SBC-201 rules, with reasoning + corrective actions.',
    oss: 'buildingSMART IDS (concept) + custom engine',
    repo: 'https://github.com/buildingSMART/IDS',
    license: 'MIT (IDS spec)',
    file: 'backend/rule_engine.py',
  },
  {
    feature: 'Floor-plan overlay (SVG)',
    capability: 'Renders parsed geometry to SVG and highlights violating rooms / setbacks in red.',
    oss: 'ezdxf geometry + custom SVG renderer',
    repo: 'https://github.com/mozman/ezdxf',
    license: 'MIT',
    file: 'backend/main.py · _render_svg',
  },
  {
    feature: 'Backend API service',
    capability: 'REST API: parse, check, run-full demo, geometry, test-data, docs.',
    oss: 'FastAPI + Uvicorn',
    repo: 'https://github.com/fastapi/fastapi',
    license: 'MIT',
    file: 'backend/main.py',
  },
  {
    feature: 'Web frontend',
    capability: 'Interactive review UI: run demo, upload, results table, overlay, docs and test data.',
    oss: 'React + Vite + Radix UI',
    repo: 'https://github.com/facebook/react',
    license: 'MIT',
    file: 'frontend/src/business.tsx',
  },
]

// ---- Inline architecture diagram (pure SVG so it exports / screenshots cleanly) ----

const GREEN = '#006B3F' // GOV.SA / Saudi green accent

function Box({
  x,
  y,
  w,
  h,
  title,
  subtitle,
  fill,
  stroke,
  titleColor,
}: {
  x: number
  y: number
  w: number
  h: number
  title: string
  subtitle?: string
  fill: string
  stroke: string
  titleColor?: string
}) {
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx={10} fill={fill} stroke={stroke} strokeWidth={1.5} />
      <text
        x={x + w / 2}
        y={subtitle ? y + h / 2 - 6 : y + h / 2 + 4}
        textAnchor='middle'
        fontSize={13}
        fontWeight={700}
        fill={titleColor || '#0f172a'}
      >
        {title}
      </text>
      {subtitle ? (
        <text x={x + w / 2} y={y + h / 2 + 13} textAnchor='middle' fontSize={11} fill='#475569'>
          {subtitle}
        </text>
      ) : null}
    </g>
  )
}

function ArchitectureDiagram() {
  return (
    <div className='w-full overflow-x-auto'>
      <svg viewBox='0 0 1080 470' className='min-w-[860px] w-full' role='img' aria-label='Architecture diagram'>
        <defs>
          <marker id='arrow' markerWidth='10' markerHeight='10' refX='8' refY='3' orient='auto' markerUnits='strokeWidth'>
            <path d='M0,0 L8,3 L0,6 Z' fill='#94a3b8' />
          </marker>
        </defs>

        {/* Column headers */}
        {[
          { x: 70, label: '1 · Inputs' },
          { x: 300, label: '2 · Open-Source Parsers' },
          { x: 545, label: '3 · Data Model' },
          { x: 730, label: '4 · Rule Engine' },
          { x: 960, label: '5 · Outputs' },
        ].map((c) => (
          <text key={c.label} x={c.x} y={30} textAnchor='middle' fontSize={12} fontWeight={700} fill={GREEN}>
            {c.label}
          </text>
        ))}

        {/* Inputs */}
        <Box x={12} y={60} w={116} h={54} title='Villa .DXF' subtitle='2D CAD plan' fill='#f1f5f9' stroke='#cbd5e1' />
        <Box x={12} y={150} w={116} h={54} title='Villa .IFC' subtitle='BIM model' fill='#f1f5f9' stroke='#cbd5e1' />
        <Box x={12} y={240} w={116} h={54} title='Submission .PDF' subtitle='vector doc' fill='#f1f5f9' stroke='#cbd5e1' />

        {/* Parsers (OSS) */}
        <Box x={215} y={60} w={170} h={54} title='ezdxf' subtitle='DXF → geometry' fill='#eff6ff' stroke='#3b82f6' titleColor='#1d4ed8' />
        <Box x={215} y={150} w={170} h={54} title='IfcOpenShell' subtitle='IFC → quantities' fill='#eff6ff' stroke='#3b82f6' titleColor='#1d4ed8' />
        <Box x={215} y={240} w={170} h={54} title='pdfplumber' subtitle='PDF → text/lines' fill='#eff6ff' stroke='#3b82f6' titleColor='#1d4ed8' />

        {/* Data model */}
        <Box
          x={470}
          y={110}
          w={150}
          h={134}
          title='Normalized'
          subtitle='setbacks · rooms · doors'
          fill='#eef2ff'
          stroke='#6366f1'
          titleColor='#4338ca'
        />

        {/* Rule engine */}
        <Box
          x={660}
          y={110}
          w={150}
          h={134}
          title='Rule Engine'
          subtitle='ADG / SBC-201'
          fill='#ecfdf5'
          stroke={GREEN}
          titleColor={GREEN}
        />
        <text x={735} y={264} textAnchor='middle' fontSize={10} fill='#475569'>
          buildingSMART IDS concept
        </text>

        {/* Outputs */}
        <Box x={860} y={90} w={200} h={54} title='Compliance Results' subtitle='PASS / FAIL + reasoning' fill='#fff7ed' stroke='#f59e0b' titleColor='#b45309' />
        <Box x={860} y={190} w={200} h={54} title='Floor-plan Overlay' subtitle='SVG, violations in red' fill='#fff7ed' stroke='#f59e0b' titleColor='#b45309' />

        {/* Arrows: inputs -> parsers */}
        <line x1={128} y1={87} x2={213} y2={87} stroke='#94a3b8' strokeWidth={1.5} markerEnd='url(#arrow)' />
        <line x1={128} y1={177} x2={213} y2={177} stroke='#94a3b8' strokeWidth={1.5} markerEnd='url(#arrow)' />
        <line x1={128} y1={267} x2={213} y2={267} stroke='#94a3b8' strokeWidth={1.5} markerEnd='url(#arrow)' />

        {/* parsers -> data model */}
        <line x1={385} y1={87} x2={468} y2={150} stroke='#94a3b8' strokeWidth={1.5} markerEnd='url(#arrow)' />
        <line x1={385} y1={177} x2={468} y2={177} stroke='#94a3b8' strokeWidth={1.5} markerEnd='url(#arrow)' />
        <line x1={385} y1={267} x2={468} y2={205} stroke='#94a3b8' strokeWidth={1.5} markerEnd='url(#arrow)' />

        {/* data model -> rule engine */}
        <line x1={620} y1={177} x2={658} y2={177} stroke='#94a3b8' strokeWidth={1.5} markerEnd='url(#arrow)' />

        {/* rule engine -> outputs */}
        <line x1={810} y1={150} x2={858} y2={117} stroke='#94a3b8' strokeWidth={1.5} markerEnd='url(#arrow)' />
        <line x1={810} y1={205} x2={858} y2={217} stroke='#94a3b8' strokeWidth={1.5} markerEnd='url(#arrow)' />

        {/* Infra band */}
        <rect x={12} y={330} width={1048} height={110} rx={12} fill='#f8fafc' stroke='#e2e8f0' strokeWidth={1.5} />
        <text x={30} y={356} fontSize={12} fontWeight={700} fill='#0f172a'>
          Platform
        </text>
        <Box x={30} y={368} w={230} h={54} title='FastAPI + Uvicorn' subtitle='Python backend service' fill='#ffffff' stroke='#cbd5e1' />
        <Box x={285} y={368} w={230} h={54} title='React + Vite + Radix UI' subtitle='Frontend review app' fill='#ffffff' stroke='#cbd5e1' />
        <Box x={540} y={368} w={230} h={54} title='IfcOpenShell / ezdxf' subtitle='geometry engines' fill='#ffffff' stroke='#cbd5e1' />
        <Box x={795} y={368} w={250} h={54} title='pdfplumber / IDS' subtitle='extraction + rule spec' fill='#ffffff' stroke='#cbd5e1' />
      </svg>
    </div>
  )
}

function ArchitectureView() {
  return (
    <div className='grid gap-6'>
      <Card>
        <CardHeader>
          <CardTitle>Architecture — Feature → Open-Source Project</CardTitle>
          <CardDescription>
            Every capability is powered by a real, named open-source project. Use this diagram to explain to
            stakeholders exactly which OSS project implements each feature.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ArchitectureDiagram />
          <div className='mt-4 flex flex-wrap gap-2 text-xs'>
            <Badge variant='outline' className='border-blue-300 text-blue-700'>Blue = OSS parsers</Badge>
            <Badge variant='outline' className='border-indigo-300 text-indigo-700'>Indigo = normalized data</Badge>
            <Badge variant='outline' className='border-emerald-300 text-emerald-700'>Green = rule engine</Badge>
            <Badge variant='outline' className='border-amber-300 text-amber-700'>Amber = outputs</Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Feature ↔ Open-Source Mapping</CardTitle>
          <CardDescription>
            Which feature uses which open-source project, its license, and the source file that integrates it.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className='overflow-hidden rounded-lg ring-1 ring-slate-200'>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Feature</TableHead>
                  <TableHead>What it does</TableHead>
                  <TableHead>Open-Source Project</TableHead>
                  <TableHead>License</TableHead>
                  <TableHead>Source file</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {FEATURES.map((f) => (
                  <TableRow key={f.feature}>
                    <TableCell className='font-medium text-slate-900'>{f.feature}</TableCell>
                    <TableCell className='text-slate-700'>{f.capability}</TableCell>
                    <TableCell>
                      <a
                        className='font-medium text-blue-700 underline underline-offset-4 hover:text-blue-900'
                        href={f.repo}
                        target='_blank'
                        rel='noreferrer'
                      >
                        {f.oss}
                      </a>
                      <div className='text-xs text-slate-500'>{f.repo}</div>
                    </TableCell>
                    <TableCell className='text-slate-700'>{f.license}</TableCell>
                    <TableCell>
                      <code className='rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-800'>{f.file}</code>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <p className='mt-4 text-sm text-slate-600'>
            Full source and README:{' '}
            <a
              className='font-medium text-blue-700 underline underline-offset-4 hover:text-blue-900'
              href='https://github.com/lifangjunone/PlansComplianceCoPilot'
              target='_blank'
              rel='noreferrer'
            >
              github.com/lifangjunone/PlansComplianceCoPilot
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

export default ArchitectureView
