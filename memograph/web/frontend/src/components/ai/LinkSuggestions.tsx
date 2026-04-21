
/**
 * LinkSuggestions - AI-powered link suggestion component
 *
 * Features:
 * - Display link suggestions with confidence scores
 * - Show bidirectional link indicators
 * - Apply/skip individual suggestions
 * - Preview linked notes on hover
 * - Real-time feedback recording
 */

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Link2, Check, X, AlertCircle, Sparkles, ArrowLeftRight, ExternalLink, Eye } from 'lucide-react';
import { aiAPI, memoriesApi } from '../../lib/api';
import type { LinkSuggestionRequest, LinkSuggestionItem } from '../../types';

interface LinkSuggestionsProps {
  content: string;
  title: string;
  noteId?: string;
  existingLinks?: string[];
  minConfidence?: number;
  maxSuggestions?: number;
  onLinkApplied?: (targetId: string, targetTitle: string) => void;
  onLinkSkipped?: (targetId: string) => void;
}

export default function LinkSuggestions({
  content,
  title,
  noteId,
  existingLinks = [],
  minConfidence = 0.4,
  maxSuggestions = 10,
  onLinkApplied,
  onLinkSkipped,
}: LinkSuggestionsProps) {
  const [appliedLinks, setAppliedLinks] = useState<Set<string>>(new Set());
  const [skippedLinks, setSkippedLinks] = useState<Set<string>>(new Set());
  const [previewId, setPreviewId] = useState<string | null>(null);

  // Fetch link suggestions
  const suggestMutation = useMutation({
    mutationFn: (request: LinkSuggestionRequest) => aiAPI.suggestLinks(request),
  });

  // Fetch preview for hovered note
  const { data: previewData } = useQuery({
    queryKey: ['memory', previewId],
    queryFn: () => (previewId ? memoriesApi.get(previewId) : null),
    enabled: !!previewId,
  });

  // Record feedback
  const feedbackMutation = useMutation({
    mutationFn: ({ targetId, accepted }: { targetId: string; accepted: boolean }) =>
      aiAPI.recordFeedback({
        feedback_type: 'link',
        item_id: targetId,
        accepted,
      }),
  });

  const handleGenerateSuggestions = () => {
    suggestMutation.mutate({
      content,
      title,
      note_id: noteId,
      existing_links: existingLinks,
      min_confidence: minConfidence,
      max_suggestions: maxSuggestions,
    });
  };

  const handleApply = (suggestion: LinkSuggestionItem) => {
    const newApplied = new Set(appliedLinks);
    newApplied.add(suggestion.target_id);
    setAppliedLinks(newApplied);

    // Remove from skipped if it was there
    const newSkipped = new Set(skippedLinks);
    newSkipped.delete(suggestion.target_id);
    setSkippedLinks(newSkipped);

    // Record feedback
    feedbackMutation.mutate({ targetId: suggestion.target_id, accepted: true });

    // Callback
    if (onLinkApplied) {
      onLinkApplied(suggestion.target_id, suggestion.target_title);
    }
  };

  const handleSkip = (suggestion: LinkSuggestionItem) => {
    const newSkipped = new Set(skippedLinks);
    newSkipped.add(suggestion.target_id);
    setSkippedLinks(newSkipped);

    // Remove from applied if it was there
    const newApplied = new Set(appliedLinks);
    newApplied.delete(suggestion.target_id);
    setAppliedLinks(newApplied);

    // Record feedback
    feedbackMutation.mutate({ targetId: suggestion.target_id, accepted: false });

    // Callback
    if (onLinkSkipped) {
      onLinkSkipped(suggestion.target_id);
    }
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.7) return 'bg-green-500';
    if (confidence >= 0.5) return 'bg-blue-500';
    if (confidence >= 0.4) return 'bg-yellow-500';
    return 'bg-gray-400';
  };

  const getConfidenceLabel = (confidence: number): string => {
    if (confidence >= 0.7) return 'High';
    if (confidence >= 0.5) return 'Medium';
    if (confidence >= 0.4) return 'Low';
    return 'Very Low';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            AI Link Suggestions
          </h3>
        </div>
        <button
          onClick={handleGenerateSuggestions}
          disabled={suggestMutation.isPending || !content.trim()}
          className="btn btn-sm btn-primary flex items-center space-x-2"
        >
          {suggestMutation.isPending ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <Link2 className="w-4 h-4" />
              <span>Suggest Links</span>
            </>
          )}
        </button>
      </div>

      {/* Error State */}
      {suggestMutation.isError && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start space-x-3 mb-4">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-red-800 dark:text-red-200">
              Failed to generate suggestions
            </h4>
            <p className="text-sm text-red-700 dark:text-red-300 mt-1">
              {suggestMutation.error instanceof Error
                ? suggestMutation.error.message
                : 'An error occurred'}
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!suggestMutation.data && !suggestMutation.isPending && !suggestMutation.isError && (
        <div className="text-center py-8">
          <Link2 className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            Click "Suggest Links" to get AI-powered link recommendations
          </p>
          <p className="text-gray-500 dark:text-gray-500 text-xs mt-1">
            Based on semantic similarity and graph analysis
          </p>
        </div>
      )}

      {/* Suggestions List */}
      {suggestMutation.data && suggestMutation.data.suggestions.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
            <span>{suggestMutation.data.total} suggestions found</span>
            <span className="flex items-center space-x-1">
              <Link2 className="w-4 h-4" />
              <span>Sorted by relevance</span>
            </span>
          </div>

          {suggestMutation.data.suggestions.map((suggestion, index) => {
            const isApplied = appliedLinks.has(suggestion.target_id);
            const isSkipped = skippedLinks.has(suggestion.target_id);

            return (
              <div
                key={index}
                className={`border rounded-lg p-4 transition-all ${
                  isApplied
                    ? 'border-green-300 bg-green-50 dark:border-green-700 dark:bg-green-900/20'
                    : isSkipped
                    ? 'border-red-300 bg-red-50 dark:border-red-700 dark:bg-red-900/20 opacity-50'
                    : 'border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700'
                }`}
                onMouseEnter={() => setPreviewId(suggestion.target_id)}
                onMouseLeave={() => setPreviewId(null)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Link Title */}
                    <div className="flex items-center space-x-2 mb-2 flex-wrap">
                      <span className="inline-flex items-center px-3 py-1 bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200 rounded-full text-sm font-medium">
                        [[{suggestion.target_title}]]
                      </span>
                      {suggestion.bidirectional && (
                        <span className="inline-flex items-center space-x-1 px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded text-xs">
                          <ArrowLeftRight className="w-3 h-3" />
                          <span>Bidirectional</span>
                        </span>
                      )}
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          suggestion.confidence >= 0.7
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : suggestion.confidence >= 0.5
                            ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                        }`}
                      >
                        {getConfidenceLabel(suggestion.confidence)}
                      </span>
                    </div>

                    {/* Confidence Bar */}
                    <div className="mb-2">
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full ${getConfidenceColor(suggestion.confidence)} transition-all`}
                            style={{ width: `${suggestion.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-600 dark:text-gray-400 font-mono min-w-[3rem] text-right">
                          {(suggestion.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    {/* Reason */}
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                      {suggestion.reason}
                    </p>

                    {/* Source */}
                    <p className="text-xs text-gray-500 dark:text-gray-500 mb-2">
                      Source: {suggestion.source}
                    </p>

                    {/* Preview */}
                    {previewId === suggestion.target_id && previewData && (
                      <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
                        <div className="flex items-center space-x-2 mb-2">
                          <Eye className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                          <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                            Preview
                          </span>
                        </div>
                        <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-3">
                          {previewData.content}
                        </p>
                        <div className="flex items-center space-x-2 mt-2">
                          <span className="text-xs text-gray-500 dark:text-gray-500">
                            {previewData.tags.length} tags
                          </span>
                          <span className="text-xs text-gray-500 dark:text-gray-500">•</span>
                          <span className="text-xs text-gray-500 dark:text-gray-500">
                            {previewData.memory_type}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-col items-center space-y-2 ml-4">
                    {!isApplied && !isSkipped && (
                      <>
                        <button
                          onClick={() => handleApply(suggestion)}
                          className="p-2 text-green-600 hover:bg-green-100 dark:text-green-400 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                          title="Apply this link"
                        >
                          <Check className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleSkip(suggestion)}
                          className="p-2 text-red-600 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                          title="Skip this link"
                        >
                          <X className="w-5 h-5" />
                        </button>
                        <a
                          href={`/memories/${suggestion.target_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 rounded-lg transition-colors"
                          title="Open in new tab"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </>
                    )}
                    {isApplied && (
                      <div className="flex items-center space-x-1 text-green-600 dark:text-green-400 text-sm">
                        <Check className="w-4 h-4" />
                        <span>Applied</span>
                      </div>
                    )}
                    {isSkipped && (
                      <div className="flex items-center space-x-1 text-red-600 dark:text-red-400 text-sm">
                        <X className="w-4 h-4" />
                        <span>Skipped</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* No Suggestions */}
      {suggestMutation.data && suggestMutation.data.suggestions.length === 0 && (
        <div className="text-center py-8">
          <Link2 className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            No link suggestions found
          </p>
          <p className="text-gray-500 dark:text-gray-500 text-xs mt-1">
            Try adjusting the minimum confidence threshold or add more content
          </p>
        </div>
      )}
    </div>
  );
}
