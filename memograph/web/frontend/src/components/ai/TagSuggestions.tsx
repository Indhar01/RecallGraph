/**
 * TagSuggestions - AI-powered tag suggestion component
 *
 * Features:
 * - Display tag suggestions with confidence scores
 * - Visual confidence bars
 * - Accept/reject individual suggestions
 * - Real-time feedback recording
 * - Loading and error states
 */

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Tag, Check, X, AlertCircle, Sparkles, TrendingUp } from 'lucide-react';
import { aiAPI } from '../../lib/api';
import type { TagSuggestionRequest, TagSuggestionItem } from '../../types';

interface TagSuggestionsProps {
  content: string;
  title: string;
  existingTags?: string[];
  minConfidence?: number;
  maxSuggestions?: number;
  onTagAccepted?: (tag: string) => void;
  onTagRejected?: (tag: string) => void;
}

export default function TagSuggestions({
  content,
  title,
  existingTags = [],
  minConfidence = 0.3,
  maxSuggestions = 5,
  onTagAccepted,
  onTagRejected,
}: TagSuggestionsProps) {
  const [acceptedTags, setAcceptedTags] = useState<Set<string>>(new Set());
  const [rejectedTags, setRejectedTags] = useState<Set<string>>(new Set());

  // Fetch tag suggestions
  const suggestMutation = useMutation({
    mutationFn: (request: TagSuggestionRequest) => aiAPI.suggestTags(request),
  });

  // Record feedback
  const feedbackMutation = useMutation({
    mutationFn: ({ tag, accepted }: { tag: string; accepted: boolean }) =>
      aiAPI.recordFeedback({
        feedback_type: 'tag',
        item_id: tag,
        accepted,
      }),
  });

  const handleGenerateSuggestions = () => {
    suggestMutation.mutate({
      content,
      title,
      existing_tags: existingTags,
      min_confidence: minConfidence,
      max_suggestions: maxSuggestions,
    });
  };

  const handleAccept = (suggestion: TagSuggestionItem) => {
    const newAccepted = new Set(acceptedTags);
    newAccepted.add(suggestion.tag);
    setAcceptedTags(newAccepted);

    // Remove from rejected if it was there
    const newRejected = new Set(rejectedTags);
    newRejected.delete(suggestion.tag);
    setRejectedTags(newRejected);

    // Record feedback
    feedbackMutation.mutate({ tag: suggestion.tag, accepted: true });

    // Callback
    if (onTagAccepted) {
      onTagAccepted(suggestion.tag);
    }
  };

  const handleReject = (suggestion: TagSuggestionItem) => {
    const newRejected = new Set(rejectedTags);
    newRejected.add(suggestion.tag);
    setRejectedTags(newRejected);

    // Remove from accepted if it was there
    const newAccepted = new Set(acceptedTags);
    newAccepted.delete(suggestion.tag);
    setAcceptedTags(newAccepted);

    // Record feedback
    feedbackMutation.mutate({ tag: suggestion.tag, accepted: false });

    // Callback
    if (onTagRejected) {
      onTagRejected(suggestion.tag);
    }
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.7) return 'bg-green-500';
    if (confidence >= 0.5) return 'bg-blue-500';
    if (confidence >= 0.3) return 'bg-yellow-500';
    return 'bg-gray-400';
  };

  const getConfidenceLabel = (confidence: number): string => {
    if (confidence >= 0.7) return 'High';
    if (confidence >= 0.5) return 'Medium';
    if (confidence >= 0.3) return 'Low';
    return 'Very Low';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            AI Tag Suggestions
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
              <Tag className="w-4 h-4" />
              <span>Suggest Tags</span>
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
          <Tag className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            Click "Suggest Tags" to get AI-powered tag recommendations
          </p>
          <p className="text-gray-500 dark:text-gray-500 text-xs mt-1">
            Based on content analysis and existing vault tags
          </p>
        </div>
      )}

      {/* Suggestions List */}
      {suggestMutation.data && suggestMutation.data.suggestions.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
            <span>{suggestMutation.data.total} suggestions found</span>
            <span className="flex items-center space-x-1">
              <TrendingUp className="w-4 h-4" />
              <span>Sorted by confidence</span>
            </span>
          </div>

          {suggestMutation.data.suggestions.map((suggestion, index) => {
            const isAccepted = acceptedTags.has(suggestion.tag);
            const isRejected = rejectedTags.has(suggestion.tag);

            return (
              <div
                key={index}
                className={`border rounded-lg p-4 transition-all ${
                  isAccepted
                    ? 'border-green-300 bg-green-50 dark:border-green-700 dark:bg-green-900/20'
                    : isRejected
                    ? 'border-red-300 bg-red-50 dark:border-red-700 dark:bg-red-900/20 opacity-50'
                    : 'border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Tag Name */}
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="inline-flex items-center px-3 py-1 bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200 rounded-full text-sm font-medium">
                        #{suggestion.tag}
                      </span>
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
                    <p className="text-xs text-gray-500 dark:text-gray-500">
                      Source: {suggestion.source}
                    </p>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center space-x-2 ml-4">
                    {!isAccepted && !isRejected && (
                      <>
                        <button
                          onClick={() => handleAccept(suggestion)}
                          className="p-2 text-green-600 hover:bg-green-100 dark:text-green-400 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                          title="Accept this tag"
                        >
                          <Check className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleReject(suggestion)}
                          className="p-2 text-red-600 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                          title="Reject this tag"
                        >
                          <X className="w-5 h-5" />
                        </button>
                      </>
                    )}
                    {isAccepted && (
                      <div className="flex items-center space-x-1 text-green-600 dark:text-green-400 text-sm">
                        <Check className="w-4 h-4" />
                        <span>Accepted</span>
                      </div>
                    )}
                    {isRejected && (
                      <div className="flex items-center space-x-1 text-red-600 dark:text-red-400 text-sm">
                        <X className="w-4 h-4" />
                        <span>Rejected</span>
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
          <Tag className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            No tag suggestions found
          </p>
          <p className="text-gray-500 dark:text-gray-500 text-xs mt-1">
            Try adjusting the minimum confidence threshold or add more content
          </p>
        </div>
      )}
    </div>
  );
}
