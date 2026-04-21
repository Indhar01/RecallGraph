import { useState, useEffect } from 'react'
import { ChevronDown, ChevronUp, X, Search, Filter } from 'lucide-react'

// ============================================================================
// Types
// ============================================================================

export interface GraphFilterState {
  minSalience: number
  maxSalience: number
  tags: string[]
  memoryTypes: string[]
  limit: number
  focusNode: string
}

interface GraphFiltersProps {
  filters: GraphFilterState
  availableTags: string[]
  onFiltersChange: (filters: GraphFilterState) => void
  onReset: () => void
  isLoadingTags?: boolean
}

// ============================================================================
// Constants
// ============================================================================

const MEMORY_TYPES = [
  { value: 'episodic', label: 'Episodic', color: '#3b82f6' },
  { value: 'semantic', label: 'Semantic', color: '#10b981' },
  { value: 'procedural', label: 'Procedural', color: '#f59e0b' },
  { value: 'fact', label: 'Fact', color: '#8b5cf6' },
]

const LIMIT_OPTIONS = [50, 100, 200, 500]

// ============================================================================
// GraphFilters Component
// ============================================================================

export default function GraphFilters({
  filters,
  availableTags,
  onFiltersChange,
  onReset,
  isLoadingTags = false,
}: GraphFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [tagSearchQuery, setTagSearchQuery] = useState('')
  const [showTagDropdown, setShowTagDropdown] = useState(false)

  // Filter available tags based on search query
  const filteredTags = availableTags.filter(
    (tag) =>
      tag.toLowerCase().includes(tagSearchQuery.toLowerCase()) &&
      !filters.tags.includes(tag)
  )

  // Update a filter value
  const updateFilter = <K extends keyof GraphFilterState>(
    key: K,
    value: GraphFilterState[K]
  ) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  // Toggle memory type selection
  const toggleMemoryType = (type: string) => {
    const newTypes = filters.memoryTypes.includes(type)
      ? filters.memoryTypes.filter((t) => t !== type)
      : [...filters.memoryTypes, type]
    updateFilter('memoryTypes', newTypes)
  }

  // Add tag to filters
  const addTag = (tag: string) => {
    if (!filters.tags.includes(tag)) {
      updateFilter('tags', [...filters.tags, tag])
      setTagSearchQuery('')
      setShowTagDropdown(false)
    }
  }

  // Remove tag from filters
  const removeTag = (tag: string) => {
    updateFilter('tags', filters.tags.filter((t) => t !== tag))
  }

  // Check if filters are active (non-default)
  const hasActiveFilters =
    filters.minSalience > 0 ||
    filters.maxSalience < 1 ||
    filters.tags.length > 0 ||
    filters.memoryTypes.length > 0 ||
    filters.limit !== 200 ||
    filters.focusNode !== ''

  // Close tag dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (!target.closest('.tag-search-container')) {
        setShowTagDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="mb-4 card">
      {/* Header */}
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center">
          <Filter className="w-5 h-5 mr-2 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
          {hasActiveFilters && (
            <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded">
              Active
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onReset()
              }}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
            >
              Reset
            </button>
          )}
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-600" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-600" />
          )}
        </div>
      </div>

      {/* Filters Content */}
      {isExpanded && (
        <div className="mt-4 space-y-4 pt-4 border-t">
          {/* Salience Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Salience Range
            </label>
            <div className="space-y-2">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <label className="text-xs text-gray-600 mb-1 block">Min</label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={filters.minSalience}
                    onChange={(e) => updateFilter('minSalience', parseFloat(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                  <div className="text-xs text-gray-600 mt-1 text-center">
                    {(filters.minSalience * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="flex-1">
                  <label className="text-xs text-gray-600 mb-1 block">Max</label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={filters.maxSalience}
                    onChange={(e) => updateFilter('maxSalience', parseFloat(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                  <div className="text-xs text-gray-600 mt-1 text-center">
                    {(filters.maxSalience * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Tags Multi-Select */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tags {isLoadingTags && <span className="text-xs text-gray-500">(loading...)</span>}
            </label>
            
            {/* Selected Tags */}
            {filters.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-2">
                {filters.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center px-2 py-1 text-sm bg-blue-100 text-blue-800 rounded"
                  >
                    {tag}
                    <button
                      onClick={() => removeTag(tag)}
                      className="ml-1 hover:text-blue-900"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}

            {/* Tag Search Input */}
            <div className="tag-search-container relative">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={tagSearchQuery}
                  onChange={(e) => {
                    setTagSearchQuery(e.target.value)
                    setShowTagDropdown(true)
                  }}
                  onFocus={() => setShowTagDropdown(true)}
                  placeholder="Search tags..."
                  className="input pl-10"
                  disabled={isLoadingTags}
                />
              </div>

              {/* Tag Dropdown */}
              {showTagDropdown && tagSearchQuery && filteredTags.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto">
                  {filteredTags.map((tag) => (
                    <button
                      key={tag}
                      onClick={() => addTag(tag)}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 transition-colors"
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Memory Type Checkboxes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Memory Types
            </label>
            <div className="space-y-2">
              {MEMORY_TYPES.map((type) => (
                <label
                  key={type.value}
                  className="flex items-center cursor-pointer hover:bg-gray-50 p-2 rounded transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={filters.memoryTypes.includes(type.value)}
                    onChange={() => toggleMemoryType(type.value)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <div
                    className="w-3 h-3 rounded-full ml-2"
                    style={{ backgroundColor: type.color }}
                  />
                  <span className="ml-2 text-sm text-gray-700">{type.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Limit Dropdown */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Node Limit
            </label>
            <select
              value={filters.limit}
              onChange={(e) => updateFilter('limit', parseInt(e.target.value))}
              className="input"
            >
              {LIMIT_OPTIONS.map((limit) => (
                <option key={limit} value={limit}>
                  {limit} nodes
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Higher limits may affect performance
            </p>
          </div>

          {/* Focus Node Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Focus Node (Optional)
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={filters.focusNode}
                onChange={(e) => updateFilter('focusNode', e.target.value)}
                placeholder="Enter node ID to focus..."
                className="input pl-10"
              />
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Shows only the specified node and its neighbors
            </p>
          </div>
        </div>
      )}
    </div>
  )
}