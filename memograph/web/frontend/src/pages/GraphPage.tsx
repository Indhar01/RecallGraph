import { useState, useCallback, useRef, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import ForceGraph2D, { ForceGraphMethods, NodeObject, LinkObject } from 'react-force-graph-2d'
import { graphAPI, searchAPI, getErrorMessage } from '../lib/api'
import { ErrorAlert } from '../components/ErrorDisplay'
import { SkeletonList } from '../components/LoadingSpinner'
import GraphFilters, { GraphFilterState } from '../components/GraphFilters'
import { Network, AlertCircle, Info } from 'lucide-react'

// ============================================================================
// Types
// ============================================================================

interface GraphNode extends NodeObject {
  id: string
  name: string
  val: number
  color: string
  memory_type: string
  salience: number
  tags: string[]
  link_count: number
  backlink_count: number
}

interface GraphLink extends LinkObject {
  source: string | GraphNode
  target: string | GraphNode
  type: string
}

interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

// ============================================================================
// Constants
// ============================================================================

const MEMORY_TYPE_COLORS: Record<string, string> = {
  episodic: '#3b82f6',    // blue
  semantic: '#10b981',     // green
  procedural: '#f59e0b',   // amber
  fact: '#8b5cf6'          // purple
}

const DEFAULT_COLOR = '#6b7280' // gray

// Default filter state
const DEFAULT_FILTERS: GraphFilterState = {
  minSalience: 0,
  maxSalience: 1,
  tags: [],
  memoryTypes: [],
  limit: 200,
  focusNode: '',
}

// ============================================================================
// GraphPage Component
// ============================================================================

export default function GraphPage() {
  const navigate = useNavigate()
  const graphRef = useRef<ForceGraphMethods>()
  const [searchParams, setSearchParams] = useSearchParams()
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  // Parse filters from URL
  const filters = useMemo((): GraphFilterState => {
    return {
      minSalience: parseFloat(searchParams.get('minSalience') || '0'),
      maxSalience: parseFloat(searchParams.get('maxSalience') || '1'),
      tags: searchParams.get('tags')?.split(',').filter(Boolean) || [],
      memoryTypes: searchParams.get('types')?.split(',').filter(Boolean) || [],
      limit: parseInt(searchParams.get('limit') || '200'),
      focusNode: searchParams.get('focus') || '',
    }
  }, [searchParams])

  // Fetch available tags for autocomplete
  const { data: availableTags = [], isLoading: isLoadingTags } = useQuery({
    queryKey: ['tags'],
    queryFn: () => searchAPI.getAllTags(),
    staleTime: 60000, // 1 minute
  })

  // Build API query parameters from filters
  const apiParams = useMemo(() => {
    const params: any = {
      limit: filters.limit,
    }

    // Add min_salience if not default (0)
    if (filters.minSalience > 0) {
      params.min_salience = filters.minSalience
    }

    // Add tags if selected
    if (filters.tags.length > 0) {
      params.tags = filters.tags.join(',')
    }

    // Add focus_node if specified
    if (filters.focusNode) {
      params.focus_node = filters.focusNode
    }

    return params
  }, [filters])

  // Fetch graph data with TanStack Query
  const { data: apiData, isLoading, error, refetch } = useQuery({
    queryKey: ['graph', apiParams],
    queryFn: () => graphAPI.getGraph(apiParams),
    staleTime: 30000, // 30 seconds
  })

  // Transform API data to ForceGraph format with client-side filtering
  const graphData: GraphData | null = useMemo(() => {
    if (!apiData) return null

    // Filter nodes based on salience range and memory types
    let filteredNodes = apiData.nodes.filter((node: any) => {
      // Filter by salience range
      if (node.salience < filters.minSalience || node.salience > filters.maxSalience) {
        return false
      }

      // Filter by memory types (if any selected)
      if (filters.memoryTypes.length > 0 && !filters.memoryTypes.includes(node.memory_type)) {
        return false
      }

      return true
    })

    // Get set of filtered node IDs
    const nodeIds = new Set(filteredNodes.map((n: any) => n.id))

    // Filter edges to only include those between filtered nodes
    const filteredEdges = apiData.edges.filter(
      (edge: any) => nodeIds.has(edge.source) && nodeIds.has(edge.target)
    )

    return {
      nodes: filteredNodes.map((node: any) => ({
        id: node.id,
        name: node.title,
        val: node.salience * 10, // Size based on salience (0-10)
        color: MEMORY_TYPE_COLORS[node.memory_type] || DEFAULT_COLOR,
        memory_type: node.memory_type,
        salience: node.salience,
        tags: node.tags,
        link_count: node.link_count,
        backlink_count: node.backlink_count,
      })),
      links: filteredEdges.map((edge: any) => ({
        source: edge.source,
        target: edge.target,
        type: edge.type,
      })),
    }
  }, [apiData, filters.minSalience, filters.maxSalience, filters.memoryTypes])

  // ============================================================================
  // Filter Handlers
  // ============================================================================

  const handleFiltersChange = useCallback((newFilters: GraphFilterState) => {
    const params = new URLSearchParams()

    // Only add non-default values to URL
    if (newFilters.minSalience > 0) {
      params.set('minSalience', newFilters.minSalience.toString())
    }
    if (newFilters.maxSalience < 1) {
      params.set('maxSalience', newFilters.maxSalience.toString())
    }
    if (newFilters.tags.length > 0) {
      params.set('tags', newFilters.tags.join(','))
    }
    if (newFilters.memoryTypes.length > 0) {
      params.set('types', newFilters.memoryTypes.join(','))
    }
    if (newFilters.limit !== 200) {
      params.set('limit', newFilters.limit.toString())
    }
    if (newFilters.focusNode) {
      params.set('focus', newFilters.focusNode)
    }

    setSearchParams(params)
  }, [setSearchParams])

  const handleResetFilters = useCallback(() => {
    setSearchParams(new URLSearchParams())
  }, [setSearchParams])

  // ============================================================================
  // Event Handlers
  // ============================================================================

  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(node)
    // Navigate to memory detail page
    navigate(`/memories/${node.id}`)
  }, [navigate])

  const handleNodeHover = useCallback((node: GraphNode | null) => {
    setHoveredNode(node)
  }, [])

  const handleBackgroundClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  // ============================================================================
  // Node Rendering
  // ============================================================================

  const paintNode = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.name
    const fontSize = 12 / globalScale
    const nodeSize = Math.sqrt(node.val || 1) * 4

    // Draw node circle
    ctx.beginPath()
    ctx.arc(node.x!, node.y!, nodeSize, 0, 2 * Math.PI, false)
    ctx.fillStyle = node.color
    ctx.fill()

    // Draw border for hovered/selected nodes
    if (hoveredNode?.id === node.id || selectedNode?.id === node.id) {
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 2 / globalScale
      ctx.stroke()
    }

    // Draw label on hover or selection
    if (hoveredNode?.id === node.id || selectedNode?.id === node.id) {
      ctx.font = `${fontSize}px Sans-Serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      
      // Draw label background
      const textWidth = ctx.measureText(label).width
      const padding = 4 / globalScale
      ctx.fillStyle = 'rgba(0, 0, 0, 0.8)'
      ctx.fillRect(
        node.x! - textWidth / 2 - padding,
        node.y! - nodeSize - fontSize - padding * 2,
        textWidth + padding * 2,
        fontSize + padding * 2
      )
      
      // Draw label text
      ctx.fillStyle = '#ffffff'
      ctx.fillText(label, node.x!, node.y! - nodeSize - fontSize)
    }
  }, [hoveredNode, selectedNode])

  // ============================================================================
  // Loading State
  // ============================================================================

  if (isLoading) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center">
              <Network className="w-8 h-8 mr-2" />
              Graph Visualization
            </h1>
            <p className="text-gray-600 mt-1">Loading graph data...</p>
          </div>
        </div>
        <div className="card">
          <SkeletonList count={3} />
        </div>
      </div>
    )
  }

  // ============================================================================
  // Error State
  // ============================================================================

  if (error) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center">
              <Network className="w-8 h-8 mr-2" />
              Graph Visualization
            </h1>
          </div>
        </div>
        <ErrorAlert
          title="Failed to load graph"
          message={getErrorMessage(error)}
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  // ============================================================================
  // Empty State
  // ============================================================================

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center">
              <Network className="w-8 h-8 mr-2" />
              Graph Visualization
            </h1>
          </div>
        </div>
        <div className="card text-center py-12">
          <AlertCircle className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No graph data available</h3>
          <p className="text-gray-600">Create some memories to visualize connections in your vault.</p>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Main Render
  // ============================================================================

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Network className="w-8 h-8 mr-2" />
            Graph Visualization
          </h1>
          <p className="text-gray-600 mt-1">
            {graphData.nodes.length} nodes • {graphData.links.length} connections
          </p>
        </div>
      </div>

      {/* Filters */}
      <GraphFilters
        filters={filters}
        availableTags={availableTags}
        onFiltersChange={handleFiltersChange}
        onReset={handleResetFilters}
        isLoadingTags={isLoadingTags}
      />

      {/* Info Banner */}
      <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-start">
        <Info className="w-5 h-5 text-blue-600 mr-3 mt-0.5 flex-shrink-0" />
        <div className="text-sm text-blue-800">
          <p className="font-medium mb-1">Interactive Graph Controls</p>
          <ul className="list-disc list-inside space-y-1">
            <li><strong>Click</strong> a node to view memory details</li>
            <li><strong>Hover</strong> over nodes to see labels</li>
            <li><strong>Drag</strong> nodes to reposition them</li>
            <li><strong>Scroll</strong> to zoom in/out</li>
            <li><strong>Drag canvas</strong> to pan around</li>
          </ul>
        </div>
      </div>

      {/* Graph Legend */}
      <div className="mb-4 card">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Memory Types</h3>
        <div className="flex flex-wrap gap-4">
          {Object.entries(MEMORY_TYPE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center">
              <div
                className="w-4 h-4 rounded-full mr-2"
                style={{ backgroundColor: color }}
              />
              <span className="text-sm text-gray-700 capitalize">{type}</span>
            </div>
          ))}
        </div>
        <div className="mt-3 pt-3 border-t text-xs text-gray-500">
          <strong>Node size</strong> represents salience (importance)
        </div>
      </div>

      {/* Hovered Node Info */}
      {hoveredNode && (
        <div className="mb-4 card bg-gray-50">
          <h3 className="font-semibold text-gray-900 mb-2">{hoveredNode.name}</h3>
          <div className="text-sm text-gray-600 space-y-1">
            <p><strong>Type:</strong> <span className="capitalize">{hoveredNode.memory_type}</span></p>
            <p><strong>Salience:</strong> {(hoveredNode.salience * 100).toFixed(0)}%</p>
            <p><strong>Connections:</strong> {hoveredNode.link_count} outgoing, {hoveredNode.backlink_count} incoming</p>
            {hoveredNode.tags.length > 0 && (
              <p><strong>Tags:</strong> {hoveredNode.tags.join(', ')}</p>
            )}
          </div>
        </div>
      )}

      {/* Force Graph */}
      <div className="card p-0 overflow-hidden" style={{ height: '600px' }}>
        <ForceGraph2D
          ref={graphRef as any}
          graphData={graphData}
          nodeLabel={() => ''} // Custom rendering via paintNode
          nodeCanvasObject={paintNode}
          nodeVal="val"
          linkColor={() => '#cbd5e1'} // gray-300
          linkWidth={1.5}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={2}
          linkDirectionalParticleSpeed={0.003}
          onNodeClick={handleNodeClick}
          onNodeHover={handleNodeHover}
          onBackgroundClick={handleBackgroundClick}
          cooldownTicks={100}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
          enableNodeDrag={true}
          enableZoomInteraction={true}
          enablePanInteraction={true}
          minZoom={0.5}
          maxZoom={8}
          backgroundColor="#ffffff"
        />
      </div>

      {/* Stats Footer */}
      <div className="mt-4 card bg-gray-50">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-gray-900">{graphData.nodes.length}</div>
            <div className="text-sm text-gray-600">Total Nodes</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">{graphData.links.length}</div>
            <div className="text-sm text-gray-600">Total Edges</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">
              {graphData.links.length > 0 
                ? (graphData.links.length / graphData.nodes.length).toFixed(1)
                : '0'}
            </div>
            <div className="text-sm text-gray-600">Avg Connections</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">
              {(graphData.nodes.reduce((sum, n) => sum + n.salience, 0) / graphData.nodes.length * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-gray-600">Avg Salience</div>
          </div>
        </div>
      </div>
    </div>
  )
}
