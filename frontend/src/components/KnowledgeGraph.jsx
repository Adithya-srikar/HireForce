import { useEffect, useRef, useState } from 'react'

// ── Color map per node group ───────────────────────────────
const GROUP_COLORS = {
  candidate:  '#7c5cfc',
  github:     '#e6edf3',
  leetcode:   '#ffa116',
  linkedin:   '#0a66c2',
  skill:      '#34d399',
  repo:       '#60a5fa',
  topic:      '#f472b6',
  stats:      '#a78bfa',
  lc_total:   '#fbbf24',
  lc_easy:    '#34d399',
  lc_medium:  '#fbbf24',
  lc_hard:    '#f87171',
  experience: '#fb923c',
  info:       '#94a3b8',
}

function groupColor(group) {
  return GROUP_COLORS[group] || '#6b7280'
}

// ── Simple force layout (no deps) ─────────────────────────
function computeLayout(nodes, edges, width, height) {
  // Initialise positions in a circle
  const n = nodes.length
  const positions = {}
  nodes.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / n
    const r = Math.min(width, height) * 0.35
    positions[node.id] = {
      x: width / 2 + r * Math.cos(angle),
      y: height / 2 + r * Math.sin(angle),
      vx: 0,
      vy: 0,
    }
  })

  const edgeMap = {}
  edges.forEach(e => {
    edgeMap[`${e.from}-${e.to}`] = true
    edgeMap[`${e.to}-${e.from}`] = true
  })

  // Run iterations
  for (let iter = 0; iter < 200; iter++) {
    // Repulsion between all pairs
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = positions[nodes[i].id]
        const b = positions[nodes[j].id]
        const dx = b.x - a.x
        const dy = b.y - a.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const force = 3000 / (dist * dist)
        const fx = (dx / dist) * force
        const fy = (dy / dist) * force
        a.vx -= fx; a.vy -= fy
        b.vx += fx; b.vy += fy
      }
    }

    // Attraction along edges
    edges.forEach(e => {
      const a = positions[e.from]
      const b = positions[e.to]
      if (!a || !b) return
      const dx = b.x - a.x
      const dy = b.y - a.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      const ideal = 120
      const force = (dist - ideal) * 0.06
      const fx = (dx / dist) * force
      const fy = (dy / dist) * force
      a.vx += fx; a.vy += fy
      b.vx -= fx; b.vy -= fy
    })

    // Centre gravity
    nodes.forEach(node => {
      const p = positions[node.id]
      p.vx += (width / 2 - p.x) * 0.008
      p.vy += (height / 2 - p.y) * 0.008
    })

    // Apply velocity with damping
    const damp = 0.85
    nodes.forEach(node => {
      const p = positions[node.id]
      p.vx *= damp; p.vy *= damp
      p.x += p.vx; p.y += p.vy
      // Clamp to canvas
      p.x = Math.max(50, Math.min(width - 50, p.x))
      p.y = Math.max(30, Math.min(height - 30, p.y))
    })
  }

  return positions
}

export default function KnowledgeGraph({ graph, studentName }) {
  const [positions, setPositions] = useState(null)
  const [tooltip, setTooltip] = useState(null)
  const [dragging, setDragging] = useState(null)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [scale, setScale] = useState(1)
  const svgRef = useRef()

  const W = 900
  const H = 600

  useEffect(() => {
    if (!graph?.nodes?.length) return
    const pos = computeLayout([...graph.nodes], graph.edges || [], W, H)
    setPositions(pos)
  }, [graph])

  if (!graph?.nodes?.length) return (
    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
      No graph data available – the candidate hasn't connected their profiles yet.
    </div>
  )

  if (!positions) return (
    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
      Computing layout…
    </div>
  )

  function onNodeMouseDown(e, nodeId) {
    e.stopPropagation()
    setDragging(nodeId)
  }

  function onSvgMouseMove(e) {
    if (!dragging) return
    const rect = svgRef.current.getBoundingClientRect()
    const x = (e.clientX - rect.left) / scale - pan.x
    const y = (e.clientY - rect.top) / scale - pan.y
    setPositions(prev => ({ ...prev, [dragging]: { ...prev[dragging], x, y, vx: 0, vy: 0 } }))
  }

  function onWheel(e) {
    e.preventDefault()
    setScale(s => Math.max(0.3, Math.min(2.5, s - e.deltaY * 0.001)))
  }

  return (
    <div style={{ position: 'relative', background: 'var(--bg)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
      {/* Legend */}
      <div style={{ position: 'absolute', top: 12, left: 12, zIndex: 10, display: 'flex', flexWrap: 'wrap', gap: 6, maxWidth: 280 }}>
        {Object.entries(GROUP_COLORS).slice(0, 8).map(([g, c]) => (
          <span key={g} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, color: 'var(--text-muted)' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: c, display: 'inline-block' }} />
            {g}
          </span>
        ))}
      </div>

      {/* Zoom hint */}
      <div style={{ position: 'absolute', top: 12, right: 12, fontSize: 11, color: 'var(--text-dim)' }}>
        Scroll to zoom · Drag nodes
      </div>

      <svg
        ref={svgRef}
        width="100%"
        viewBox={`0 0 ${W} ${H}`}
        style={{ display: 'block', cursor: dragging ? 'grabbing' : 'default', maxHeight: 600 }}
        onMouseMove={onSvgMouseMove}
        onMouseUp={() => setDragging(null)}
        onMouseLeave={() => setDragging(null)}
        onWheel={onWheel}
      >
        <defs>
          <marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 z" fill="rgba(255,255,255,0.15)" />
          </marker>
          {/* Glow filter for candidate node */}
          <filter id="glow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        <g transform={`scale(${scale}) translate(${pan.x},${pan.y})`}>
          {/* Edges */}
          {(graph.edges || []).map((edge, i) => {
            const a = positions[edge.from]
            const b = positions[edge.to]
            if (!a || !b) return null
            return (
              <g key={i}>
                <line
                  x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                  stroke="rgba(255,255,255,0.08)"
                  strokeWidth={edge.width || 1}
                  markerEnd="url(#arrow)"
                />
                {edge.label && (
                  <text
                    x={(a.x + b.x) / 2}
                    y={(a.y + b.y) / 2}
                    fill="rgba(255,255,255,0.25)"
                    fontSize={9}
                    textAnchor="middle"
                    dominantBaseline="middle"
                  >
                    {edge.label}
                  </text>
                )}
              </g>
            )
          })}

          {/* Nodes */}
          {graph.nodes.map(node => {
            const p = positions[node.id]
            if (!p) return null
            const r = Math.max(10, (node.size || 20) * 0.6)
            const color = groupColor(node.group)
            const isCandidate = node.group === 'candidate'

            return (
              <g
                key={node.id}
                transform={`translate(${p.x},${p.y})`}
                style={{ cursor: 'grab' }}
                onMouseDown={e => onNodeMouseDown(e, node.id)}
                onMouseEnter={() => setTooltip({ ...node, x: p.x, y: p.y })}
                onMouseLeave={() => setTooltip(null)}
              >
                <circle
                  r={r}
                  fill={color}
                  fillOpacity={isCandidate ? 1 : 0.85}
                  stroke={isCandidate ? '#fff' : color}
                  strokeWidth={isCandidate ? 2 : 1}
                  filter={isCandidate ? 'url(#glow)' : undefined}
                />
                <text
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill={isCandidate ? '#fff' : '#0b0c10'}
                  fontSize={Math.min(r * 0.75, 11)}
                  fontWeight={isCandidate ? 700 : 500}
                  style={{ pointerEvents: 'none', userSelect: 'none' }}
                >
                  {node.label.length > 12 ? node.label.slice(0, 11) + '…' : node.label}
                </text>
              </g>
            )
          })}
        </g>

        {/* Tooltip */}
        {tooltip && (
          <foreignObject
            x={Math.min(tooltip.x * scale + 10, W - 200)}
            y={Math.max(tooltip.y * scale - 60, 10)}
            width={200}
            height={70}
            style={{ pointerEvents: 'none' }}
          >
            <div
              xmlns="http://www.w3.org/1999/xhtml"
              style={{
                background: 'rgba(17,19,24,0.95)',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: 8,
                padding: '8px 12px',
                fontSize: 12,
                color: '#e8eaf0',
                boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              }}
            >
              <strong style={{ color: groupColor(tooltip.group) }}>{tooltip.label}</strong>
              <div style={{ color: '#7a7f95', marginTop: 2, fontSize: 11 }}>{tooltip.title}</div>
            </div>
          </foreignObject>
        )}
      </svg>
    </div>
  )
}
