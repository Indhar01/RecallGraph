
/**
 * KnowledgeAnalysis - Comprehensive knowledge base analysis dashboard
 *
 * Features:
 * - Dashboard with summary statistics
 * - Topic clusters visualization
 * - Knowledge gaps overview
 * - Learning paths recommendations
 * - Comprehensive analysis view
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Brain, 
  Sparkles, 
  TrendingUp, 
  BookOpen,
  Network,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  XCircle
} from 'lucide-react';
import { aiAPI } from '../../lib/api';

interface KnowledgeAnalysisProps {
  autoLoad?: boolean;
}

export default function KnowledgeAnalysis({
  autoLoad = false,
}: KnowledgeAnalysisProps) {
  const [selectedTab, setSelectedTab] = useState<'overview' | 'clusters' | 'gaps' | 'paths'>('overview');

  // Fetch comprehensive analysis
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['knowledge-analysis'],
    queryFn: () => aiAPI.analyzeKnowledgeBase(),
    enabled: autoLoad,
  });

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Brain },
    { id: 'clusters', label: 'Topic Clusters', icon: Network },
    { id: 'gaps', label: 'Knowledge Gaps', icon: AlertTriangle },
    { id: 'paths', label: 'Learning Paths', icon: BookOpen },
  ] as const;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Knowledge Base Analysis
          </h2>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className="btn btn-primary flex items-center space-x-2"
        >
          {isLoading ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <RefreshCw className="w-5 h-5" />
              <span>Analyze</span>
            </>
          )}
        </button>
      </div>

      {/* Error State */}
      {isError && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start space-x-3">
          <XCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-red-800 dark:text-red-200">
              Analysis failed
            </h4>
            <p className="text-sm text-red-700 dark:text-red-300 mt-1">
              {error instanceof Error ? error.message : 'An error occurred'}
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!data && !isLoading && !isError && (
        <div className="text-center py-12">
          <Brain className="w-16 h-16 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400 text-lg font-medium">
            Analyze Your Knowledge Base
          </p>
          <p className="text-gray-500 dark:text-gray-500 text-sm mt-2">
            Get comprehensive insights into your vault's structure, gaps, and learning opportunities
          </p>
          <button
            onClick={() => refetch()}
            className="mt-6 btn btn-primary flex items-center space-x-2 mx-auto"
          >
            <Brain className="w-5 h-5" />
            <span>Start Analysis</span>
          </button>
        </div>
      )}

      {/* Analysis Results */}
      {data && (
        <>
          {/* Tabs */}
          <div className="flex space-x-2 mb-6 border-b border-gray-200 dark:border-gray-700">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setSelectedTab(tab.id)}
                  className={`flex items-center space-x-2 px-4 py-2 border-b-2 transition-colors ${
                    selectedTab === tab.id
                      ? 'border-primary-600 text-primary-600 dark:text-primary-400'
                      : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Overview Tab */}
          {selectedTab === 'overview' && (
            <div className="space-y-6">
              {/* Summary Statistics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 rounded-lg p-4 border border-red-200 dark:border-red-800">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-2xl font-bold text-red-900 dark:text-red-100">
                        {data.summary.total_gaps}
                      </div>
                      <div className="text-sm text-red-700 dark:text-red-300 mt-1">
                        Knowledge Gaps
                      </div>
                    </div>
                    <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
                  </div>
                </div>

                <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-2xl font-bold text-orange-900 dark:text-orange-100">
                        {(data.summary.avg_severity * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm text-orange-700 dark:text-orange-300 mt-1">
                        Avg Severity
                      </div>
                    </div>
                    <TrendingUp className="w-8 h-8 text-orange-600 dark:text-orange-400" />
                  </div>
                </div>

                <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                        {data.summary.total_clusters}
                      </div>
                      <div className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                        Topic Clusters
                      </div>
                    </div>
                    <Network className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                  </div>
                </div>

                <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-2xl font-bold text-green-900 dark:text-green-100">
                        {data.summary.total_paths}
                      </div>
                      <div className="text-sm text-green-700 dark:text-green-300 mt-1">
                        Learning Paths
                      </div>
                    </div>
                    <BookOpen className="w-8 h-8 text-green-600 dark:text-green-400" />
                  </div>
                </div>
              </div>

              {/* Gap Type Distribution */}
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Gap Type Distribution
                </h3>
                <div className="space-y-2">
                  {Object.entries(data.summary.gap_types).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between">
                      <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">
                        {type.replace('_', ' ')}
                      </span>
                      <div className="flex items-center space-x-2">
                        <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-primary-600 h-2 rounded-full"
                            style={{ width: `${(count / data.summary.total_gaps) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100 min-w-[2rem] text-right">
                          {count}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Clusters Tab */}
          {selectedTab === 'clusters' && (
            <div className="space-y-4">
              {data.clusters.length > 0 ? (
                data.clusters.map((cluster, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:border-primary-300 dark:hover:border-primary-700 transition-all"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                          <Network className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                          <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                            {cluster.topic}
                          </h4>
                          <div className="flex items-center space-x-4 mt-1">
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                              {cluster.size} notes
                            </span>
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                              Cohesion: {(cluster.cohesion * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {cluster.notes.slice(0, 10).map((note, nIndex) => (
                        <span
                          key={nIndex}
                          className="inline-flex items-center px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm"
                        >
                          {note}
                        </span>
                      ))}
                      {cluster.notes.length > 10 && (
                        <span className="inline-flex items-center px-3 py-1 bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-400 rounded-full text-sm">
                          +{cluster.notes.length - 10} more
                        </span>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <Network className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-600 dark:text-gray-400">
                    No topic clusters identified
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Gaps Tab */}
          {selectedTab === 'gaps' && (
            <div className="space-y-3">
              {data.gaps.length > 0 ? (
                data.gaps.slice(0, 10).map((gap, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                        {gap.title}
                      </h4>
                      <span
                        className={`px-2 py-1 rounded text-xs text-white ${
                          gap.severity >= 0.7
                            ? 'bg-red-600'
                            : gap.severity >= 0.5
                            ? 'bg-orange-600'
                            : 'bg-yellow-600'
                        }`}
                      >
                        {(gap.severity * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {gap.description}
                    </p>
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <AlertTriangle className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-600 dark:text-gray-400">
                    No knowledge gaps detected
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Paths Tab */}
          {selectedTab === 'paths' && (
            <div className="space-y-4">
              {data.learning_paths.length > 0 ? (
                data.learning_paths.map((path, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:border-primary-300 dark:hover:border-primary-700 transition-all"
                  >
                    <div className="flex items-start space-x-3 mb-3">
                      <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                        <BookOpen className="w-5 h-5 text-green-600 dark:text-green-400" />
                      </div>
                      <div className="flex-1">
                        <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
                          {path.topic}
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                          {path.description}
                        </p>
                        <div className="flex items-center space-x-2">
                          {path.notes.map((note, nIndex) => (
                            <div key={nIndex} className="flex items-center">
                              <span className="px-3 py-1 bg-primary-100 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 rounded-full text-sm">
                                {note}
                              </span>
                              {nIndex < path.notes.length - 1 && (
                                <ArrowRight className="w-4 h-4 text-gray-400 dark:text-gray-600 mx-2" />
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <BookOpen className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-600 dark:text-gray-400">
                    No learning paths identified
                  </p>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}