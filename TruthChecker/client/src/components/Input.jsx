import React, { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useTheme } from '../context/ThemeContext';
import { predictText, predictUrl, correctFeedback } from '../services/api';
import ProbabilityGauge from './ProbabilityGauge';
import ShareModal from './ShareModal';

// Loading step definitions
const LOADING_STEPS = [
  { icon: '📥', label: 'Extracting article content...' },
  { icon: '🤖', label: 'Running ML model analysis...' },
  { icon: '🔍', label: 'Searching trusted sources...' },
  { icon: '📊', label: 'Calculating final score...' },
];

const Input = () => {
  const [inputType, setInputType] = useState('text');
  const [text, setText] = useState('');
  const [url, setUrl] = useState('');
  const [loadingStep, setLoadingStep] = useState(0);
  const [feedbackStatus, setFeedbackStatus] = useState(null); // null | 'confirmed' | 'corrected' | 'sending'
  const [showShareModal, setShowShareModal] = useState(false);
  const { theme } = useTheme();

  // TanStack Query mutation for text prediction
  const textMutation = useMutation({
    mutationFn: predictText,
  });

  // TanStack Query mutation for URL prediction
  const urlMutation = useMutation({
    mutationFn: predictUrl,
  });

  // Active mutation based on input type
  const mutation = inputType === 'text' ? textMutation : urlMutation;
  const result = mutation.data || null;
  const loading = mutation.isPending;
  const error = mutation.error;

  // Animate loading steps
  useEffect(() => {
    if (!loading) {
      setLoadingStep(0);
      return;
    }

    setLoadingStep(0);
    const interval = setInterval(() => {
      setLoadingStep(prev => {
        if (prev < LOADING_STEPS.length - 1) return prev + 1;
        return prev;
      });
    }, 2500);

    return () => clearInterval(interval);
  }, [loading]);

  const handleTypeChange = (type) => {
    setInputType(type);
    setText('');
    setUrl('');
    setFeedbackStatus(null);
    textMutation.reset();
    urlMutation.reset();
  };

  const handleAnalyze = () => {
    const currentInput = inputType === 'text' ? text.trim() : url.trim();

    if (!currentInput) return;

    if (inputType === 'url' && !isValidUrl(currentInput)) return;

    if (inputType === 'text') {
      textMutation.mutate(currentInput);
    } else {
      urlMutation.mutate(currentInput);
    }
    setFeedbackStatus(null);
  };

  const isValidUrl = (string) => {
    try {
      new URL(string);
      return true;
    } catch (_) {
      return false;
    }
  };

  // Handle user feedback (thumbs up/down)
  const handleFeedback = async (isCorrect) => {
    if (!result?.prediction_id || feedbackStatus) return;

    if (isCorrect) {
      setFeedbackStatus('confirmed');
      return;
    }

    // Thumbs down — flip the verdict
    const correctedVerdict = result.prediction === 'True' ? 'Fake' : 'True';
    setFeedbackStatus('sending');

    try {
      await correctFeedback(result.prediction_id, correctedVerdict);
      setFeedbackStatus('corrected');
    } catch (err) {
      console.error('Feedback correction failed:', err);
      setFeedbackStatus(null);
    }
  };


  return (
    <div className='flex flex-col justify-center items-center text-center px-[16px] md:px-[32px] lg:px-[58px] mt-[32px]'>
      <div className='max-w-[800px] w-full glass-panel p-[30px] rounded-2xl'>

        {/* Toggle Buttons */}
        <div className='flex mb-6 bg-[var(--bg-deep)] rounded-xl p-1.5 border border-[var(--border-color)]'>
          <button
            onClick={() => handleTypeChange('text')}
            className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
              inputType === 'text'
                ? 'bg-[var(--primary-accent)] text-white shadow-lg shadow-green-900/20'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-primary)]'
            }`}
          >
            Text Input
          </button>
          <button
            onClick={() => handleTypeChange('url')}
            className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
              inputType === 'url'
                 ? 'bg-[var(--primary-accent)] text-white shadow-lg shadow-green-900/20'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-primary)]'
            }`}
          >
            URL Input
          </button>
        </div>

        {/* Input Field */}
        {inputType === 'text' ? (
          <textarea
            placeholder='Paste your news article or headline here...'
            rows={8}
            cols={60}
            value={text}
            onChange={(e) => setText(e.target.value)}
            className='bg-[var(--bg-primary)] border border-[var(--border-color)] p-[16px] placeholder:text-sm placeholder:text-[var(--text-muted)] outline-none rounded-xl w-full resize-none text-[var(--text-primary)] transition-all duration-300 focus:ring-2 focus:ring-[var(--primary-accent)] focus:border-transparent'
          />
        ) : (
          <input
            type='url'
            placeholder='Enter news article URL here... (e.g., https://example.com/article)'
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className='bg-[var(--bg-primary)] border border-[var(--border-color)] p-[16px] placeholder:text-sm placeholder:text-[var(--text-muted)] outline-none rounded-xl w-full text-[var(--text-primary)] transition-all duration-300 focus:ring-2 focus:ring-[var(--primary-accent)] focus:border-transparent'
          />
        )}

        {/* Animated Loading Steps */}
        {loading && (
          <div className='w-full mt-6 mb-2'>
            <div className='space-y-3'>
              {LOADING_STEPS.map((step, index) => (
                <div
                  key={index}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg border border-transparent transition-all duration-500 ${
                    index <= loadingStep ? 'opacity-100' : 'opacity-0 translate-y-2'
                  }`}
                  style={{
                    transitionDelay: `${index * 100}ms`,
                    backgroundColor: index < loadingStep
                      ? 'var(--step-done-bg)'
                      : index === loadingStep
                        ? 'var(--step-active-bg)'
                        : 'transparent',
                    borderColor: index === loadingStep ? 'var(--primary-accent)' : 'transparent'
                  }}
                >
                  {/* Icon: checkmark if done, spinner if active, dot if pending */}
                  <span className='text-lg w-6 text-center'>
                    {index < loadingStep ? (
                      <span className='text-[var(--text-success)] font-bold'>✓</span>
                    ) : index === loadingStep ? (
                      <span className='inline-block animate-spin-slow text-[var(--primary-accent)]'>⟳</span>
                    ) : (
                      <span className='text-[var(--text-muted)] opacity-50'>{step.icon}</span>
                    )}
                  </span>
                  <span className={`text-sm ${
                    index < loadingStep
                      ? 'text-[var(--text-success)] font-medium'
                      : index === loadingStep
                        ? 'text-[var(--text-primary)] font-bold'
                        : 'text-[var(--text-muted)]'
                  }`}>
                    {index < loadingStep ? step.label.replace('...', ' ✔') : step.label}
                  </span>
                </div>
              ))}
            </div>
            {/* Progress bar underneath */}
            <div className='w-full h-[4px] relative overflow-hidden rounded-full bg-[var(--bg-deep)] mt-4'>
              <div
                className='absolute inset-y-0 left-0 bg-gradient-to-r from-green-400 to-emerald-600 rounded-full transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(34,197,94,0.5)]'
                style={{ width: `${((loadingStep + 1) / LOADING_STEPS.length) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Button */}
        <div className='w-full flex justify-center items-center'>
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className='btn-primary bg-[var(--primary-accent)] py-3 px-16 rounded-xl text-white font-bold text-lg mt-[24px] hover:brightness-110 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none'
          >
            {loading ? 'Analyzing...' : 'Analyze News'}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className='mt-6 bg-[var(--bg-primary)] p-4 rounded-md text-center'>
            <p className='text-red-500'>
              {error?.response?.data?.error || error?.message || 'Could not connect to the server. Make sure the Django API is running on port 8000.'}
            </p>
          </div>
        )}

        {/* Output Display */}
        {result && !loading && (
          <div className='mt-6 bg-[var(--bg-primary)] p-4 rounded-md text-left text-[var(--text-primary)]'>
            {result.error ? (
              <p className='text-[var(--text-error)] text-center'>{result.error}</p>
            ) : (
              <>
                {/* Probability Gauge — with animated reveal */}
                <div className='animate-fadeSlideIn'>
                  <ProbabilityGauge
                    probability={result.probability}
                    confidenceLabel={result.confidence_label}
                  />
                </div>

                {/* Source Verification Section */}
                {result.verification_enabled && (
                  <div className='mt-5 pt-4 border-t border-[var(--border-color)] animate-fadeSlideIn' style={{ animationDelay: '200ms' }}>
                    <div className='flex items-center gap-2 mb-3'>
                      <span className='text-lg'>🔍</span>
                      <h3 className='text-sm font-semibold text-[var(--text-primary)]'>Source Verification Analysis</h3>
                      {result.search_insufficient ? (
                        <span className='bg-[var(--badge-cyan-bg)] text-[var(--badge-cyan-text)] text-xs px-2 py-0.5 rounded-full border border-[var(--badge-cyan-border)] font-medium'>
                          ⚡ Search limited — using ML model
                        </span>
                      ) : result.trusted_count > 0 ? (
                        <span className='bg-[var(--card-green)] text-[var(--text-success)] text-xs px-2 py-0.5 rounded-full border border-[var(--card-green-border)] font-medium'>
                          ✓ {result.trusted_count} trusted source{result.trusted_count > 1 ? 's' : ''} found
                        </span>
                      ) : (
                        <span className='bg-yellow-900/20 text-[var(--text-warning)] text-xs px-2 py-0.5 rounded-full border border-yellow-700/30 font-medium'>
                          ⚠ No trusted sources found
                        </span>
                      )}
                    </div>

                    {/* ML vs Source Score */}
                    <div className='grid grid-cols-2 gap-3 mb-4'>
                      <div className='bg-[var(--card-blue)] p-3 rounded-lg border border-[var(--card-blue-border)]'>
                        <p className='text-xs text-[var(--text-secondary)] mb-1'>ML Model Score</p>
                        <p className='text-lg font-bold text-[var(--text-info)]'>{(result.ml_score * 100).toFixed(1)}%</p>
                        <p className='text-xs text-[var(--text-muted)]'>Weight: {(result.ml_weight * 100)}%</p>
                      </div>
                      <div className='bg-[var(--card-green)] p-3 rounded-lg border border-[var(--card-green-border)]'>
                        <p className='text-xs text-[var(--text-secondary)] mb-1'>Source Score</p>
                        <p className='text-lg font-bold text-[var(--text-success)]'>{(result.source_score * 100).toFixed(1)}%</p>
                        <p className='text-xs text-[var(--text-muted)]'>Weight: {(result.source_weight * 100)}%</p>
                      </div>
                    </div>

                    {/* 3 Signal Breakdown */}
                    <div className='bg-[var(--bg-deep)] p-3 rounded-lg border border-[var(--border-color)] mb-3'>
                      <p className='text-xs text-[var(--text-secondary)] mb-3 font-medium'>Source Score Breakdown (3 Signals)</p>

                      {/* Signal 1: Coverage Density */}
                      <div className='mb-3'>
                        <div className='flex justify-between items-center mb-1'>
                          <span className='text-xs text-[var(--text-secondary)]'>📡 Coverage Density</span>
                          <span className='text-xs font-mono text-[var(--text-primary)]'>{(result.signal_coverage * 100).toFixed(1)}%</span>
                        </div>
                        <div className='w-full h-1.5 bg-[var(--bg-primary)] rounded-full overflow-hidden'>
                          <div
                            className='h-full rounded-full transition-all duration-1000'
                            style={{
                              width: `${result.signal_coverage * 100}%`,
                              backgroundColor: result.signal_coverage > 0.5 ? 'var(--text-success)' : result.signal_coverage > 0.2 ? 'var(--text-warning)' : 'var(--text-error)'
                            }}
                          />
                        </div>
                        <p className='text-[10px] text-[var(--text-muted)] mt-0.5'>How widely is this story covered online? (sigmoid of search results)</p>
                      </div>

                      {/* Signal 2: Trusted Ratio */}
                      <div className='mb-3'>
                        <div className='flex justify-between items-center mb-1'>
                          <span className='text-xs text-[var(--text-secondary)]'>🛡️ Trusted Source Ratio</span>
                          <span className='text-xs font-mono text-[var(--text-primary)]'>{(result.signal_trust_ratio * 100).toFixed(1)}%</span>
                        </div>
                        <div className='w-full h-1.5 bg-[var(--bg-primary)] rounded-full overflow-hidden'>
                          <div
                            className='h-full rounded-full transition-all duration-1000'
                            style={{
                              width: `${result.signal_trust_ratio * 100}%`,
                              backgroundColor: result.signal_trust_ratio > 0.3 ? 'var(--text-success)' : result.signal_trust_ratio > 0.1 ? 'var(--text-warning)' : 'var(--text-error)'
                            }}
                          />
                        </div>
                        <p className='text-[10px] text-[var(--text-muted)] mt-0.5'>What fraction of results come from verified news outlets? ({result.trusted_count}/{result.total_results})</p>
                      </div>

                      {/* Signal 3: Content Relevance */}
                      <div>
                        <div className='flex justify-between items-center mb-1'>
                          <span className='text-xs text-[var(--text-secondary)]'>🎯 Content Relevance</span>
                          <span className='text-xs font-mono text-[var(--text-primary)]'>{(result.signal_relevance * 100).toFixed(1)}%</span>
                        </div>
                        <div className='w-full h-1.5 bg-[var(--bg-primary)] rounded-full overflow-hidden'>
                          <div
                            className='h-full rounded-full transition-all duration-1000'
                            style={{
                              width: `${result.signal_relevance * 100}%`,
                              backgroundColor: result.signal_relevance > 0.3 ? 'var(--text-success)' : result.signal_relevance > 0.1 ? 'var(--text-warning)' : 'var(--text-error)'
                            }}
                          />
                        </div>
                        <p className='text-[10px] text-[var(--text-muted)] mt-0.5'>Are search results about the same topic? (Overlap Coefficient)</p>
                      </div>
                    </div>

                    {/* Trusted Sources List */}
                    {result.trusted_sources && result.trusted_sources.length > 0 && (
                      <div className='mt-3'>
                        <p className='text-xs text-[var(--text-secondary)] mb-2'>Verified by trusted sources:</p>
                        <div className='space-y-2 max-h-[200px] overflow-y-auto'>
                          {result.trusted_sources.map((source, i) => (
                            <a
                              key={i}
                              href={source.url}
                              target='_blank'
                              rel='noopener noreferrer'
                              className='block bg-[var(--bg-deep)] p-2.5 rounded-lg border border-[var(--border-color)] hover:border-green-700 transition group'
                            >
                              <div className='flex items-start gap-2'>
                                <span className='text-green-500 text-xs mt-0.5'>✓</span>
                                <div className='flex-1 min-w-0'>
                                  <p className='text-xs font-medium text-[var(--text-primary)] truncate group-hover:text-[var(--text-success)] transition'>
                                    {source.name}
                                  </p>
                                  <p className='text-xs text-[var(--text-info)] truncate'>{source.domain}</p>
                                  {source.snippet && (
                                    <p className='text-xs text-[var(--text-muted)] mt-1 line-clamp-2'>{source.snippet}</p>
                                  )}
                                </div>
                              </div>
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Feedback Learning Indicator */}
                {result.verification_enabled && (
                  <div className='mt-3 pt-3 border-t border-[var(--border-color)] animate-fadeSlideIn' style={{ animationDelay: '400ms' }}>
                    <div className='flex items-center justify-between'>
                      <div className='flex items-center gap-2'>
                        <span className='text-sm'>🧠</span>
                        <span className='text-xs text-[var(--text-secondary)]'>
                          Feedback Learning
                        </span>
                        <span className='bg-[var(--badge-purple-bg)] text-[var(--badge-purple-text)] text-[10px] px-1.5 py-0.5 rounded border border-[var(--badge-purple-border)]'>
                          {result.db_total || 0} articles in database
                        </span>
                      </div>
                      {result.history_applied && (
                        <span className='bg-[var(--badge-cyan-bg)] text-[var(--badge-cyan-text)] text-[10px] px-1.5 py-0.5 rounded border border-[var(--badge-cyan-border)]'>
                          ✓ History applied ({result.similar_count} similar)
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Detailed Stats */}
                <div className='mt-4 pt-4 border-t border-[var(--border-color)] grid grid-cols-2 gap-4 text-sm animate-fadeSlideIn' style={{ animationDelay: '600ms' }}>
                  <div>
                    <span className='text-[var(--text-secondary)]'>Prediction:</span>
                    <span className={`ml-2 font-bold ${result.prediction === 'True' ? 'text-[var(--text-success)]' : 'text-[var(--text-error)]'}`}>
                      {result.prediction} News
                    </span>
                  </div>
                  <div>
                    <span className='text-[var(--text-secondary)]'>Confidence:</span>
                    <span className='ml-2 text-[var(--text-primary)]'>{result.confidence_level}</span>
                  </div>
                  <div>
                    <span className='text-[var(--text-secondary)]'>Combined Score:</span>
                    <span className='ml-2 text-[var(--text-primary)]'>{(result.probability * 100).toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className='text-[var(--text-secondary)]'>Text Length:</span>
                    <span className='ml-2 text-[var(--text-primary)]'>{result.text_length} chars</span>
                  </div>
                  {result.source && (
                    <div className='col-span-2'>
                      <span className='text-[var(--text-secondary)]'>Source:</span>
                      <a href={result.source} target='_blank' rel='noopener noreferrer' className='ml-2 text-[var(--text-info)] hover:underline truncate block'>
                        {result.source}
                      </a>
                    </div>
                  )}
                  {result.title && (
                    <div className='col-span-2'>
                      <span className='text-[var(--text-secondary)]'>Title:</span>
                      <span className='ml-2 text-[var(--text-primary)]'>{result.title}</span>
                    </div>
                  )}
                </div>

                {/* User Feedback Buttons */}
                {result.prediction_id && (
                  <div className='mt-4 pt-4 border-t border-[var(--border-color)] animate-fadeSlideIn' style={{ animationDelay: '700ms' }}>
                    <div className='flex items-center justify-between'>
                      <p className='text-xs text-[var(--text-secondary)]'>Was this prediction correct?</p>
                      <div className='flex items-center gap-2'>
                        {feedbackStatus === null && (
                          <>
                            <button
                              onClick={() => handleFeedback(true)}
                              className='flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[var(--text-success)] bg-[var(--card-green)] text-[var(--text-success)] text-xs hover:bg-green-500/20 transition cursor-pointer'
                              title='Yes, prediction is correct'
                            >
                              👍 Correct
                            </button>
                            <button
                              onClick={() => handleFeedback(false)}
                              className='flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[var(--text-error)] bg-[var(--card-red)] text-[var(--text-error)] text-xs hover:bg-red-500/20 transition cursor-pointer'
                              title='No, prediction is wrong — fix it'
                            >
                              👎 Wrong
                            </button>
                          </>
                        )}
                        {feedbackStatus === 'sending' && (
                          <span className='text-xs text-[var(--text-muted)]'>Correcting...</span>
                        )}
                        {feedbackStatus === 'confirmed' && (
                          <span className='text-xs text-[var(--text-success)]'>✓ Thanks! Prediction confirmed.</span>
                        )}
                        {feedbackStatus === 'corrected' && (
                          <span className='text-xs text-[var(--text-warning)]'>✓ Corrected! Future predictions improved.</span>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Share Result Button */}
                <div className='mt-4 pt-4 border-t border-[var(--border-color)] animate-fadeSlideIn' style={{ animationDelay: '800ms' }}>
                  <button
                    onClick={() => setShowShareModal(true)}
                    className='w-full py-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-bold text-sm hover:brightness-110 transition cursor-pointer flex items-center justify-center gap-2 shadow-lg shadow-purple-900/20'
                  >
                    <span>📢</span> Share This Result
                  </button>
                  <p className='text-[10px] text-[var(--text-muted)] text-center mt-1.5'>
                    Share on WhatsApp, Facebook, X or with the TruthChecker community
                  </p>
                </div>
              </>
            )}

            {/* Share Modal */}
            <ShareModal
              isOpen={showShareModal}
              onClose={() => setShowShareModal(false)}
              predictionData={{
                text: inputType === 'text' ? text : (result?.title || url),
                prediction: result?.prediction,
                probability: result?.probability,
                confidence_label: result?.confidence_label,
                source: result?.source || '',
                ml_score: result?.ml_score,
                source_score: result?.source_score,
                trusted_count: result?.trusted_count,
                total_results: result?.total_results,
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default Input;