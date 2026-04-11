import React, { useState } from 'react';
import { createCommunityPost } from '../services/api';

const CATEGORIES = ['General', 'Health', 'Technology', 'Politics', 'Finance', 'Entertainment', 'Science', 'Sports'];

/**
 * ShareModal - Appears after prediction to share results via social media or community.
 * 
 * Props:
 *   isOpen: boolean
 *   onClose: () => void
 *   predictionData: { text, prediction, probability, confidence_label, source, ml_score, source_score, trusted_count, total_results }
 */
const ShareModal = ({ isOpen, onClose, predictionData }) => {
  const [category, setCategory] = useState('General');
  const [shareStatus, setShareStatus] = useState(null); // null | 'sharing' | 'success' | 'error'
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen || !predictionData) return null;

  const verdict = predictionData.prediction;
  const probability = predictionData.probability;
  const confidenceLabel = predictionData.confidence_label || '';
  const isFake = verdict === 'Fake';

  // Build share text
  const verdictEmoji = isFake ? '🚨' : '✅';
  const shareText = `${verdictEmoji} AI Verdict: This news is ${verdict} (${(probability * 100).toFixed(1)}% confidence)\n\nChecked with TruthChecker AI - Detect fake news instantly!`;

  // Social share URLs
  const encodedText = encodeURIComponent(shareText);
  const encodedUrl = encodeURIComponent(predictionData.source || window.location.origin);

  const socialLinks = [
    {
      name: 'WhatsApp',
      icon: '💬',
      color: '#25D366',
      url: `https://wa.me/?text=${encodedText}%20${encodedUrl}`,
    },
    {
      name: 'Facebook',
      icon: '📘',
      color: '#1877F2',
      url: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}&quote=${encodedText}`,
    },
    {
      name: 'X (Twitter)',
      icon: '𝕏',
      color: '#000000',
      url: `https://twitter.com/intent/tweet?text=${encodedText}&url=${encodedUrl}`,
    },
    {
      name: 'LinkedIn',
      icon: '💼',
      color: '#0A66C2',
      url: `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`,
    },
  ];

  const handleShareWithCommunity = async () => {
    setShareStatus('sharing');
    setErrorMsg('');

    try {
      // Extract title from the text (first line or first 100 chars)
      const lines = predictionData.text?.split('\n') || [];
      const title = lines[0]?.substring(0, 100) || predictionData.text?.substring(0, 100) || 'Untitled';

      await createCommunityPost({
        title,
        text: predictionData.text || '',
        verdict: predictionData.prediction,
        probability: predictionData.probability,
        confidence_label: predictionData.confidence_label || '',
        source_url: predictionData.source || '',
        category,
        ml_score: predictionData.ml_score || 0.5,
        source_score: predictionData.source_score || 0.5,
        trusted_count: predictionData.trusted_count || 0,
        total_results: predictionData.total_results || 0,
      });

      setShareStatus('success');
      setTimeout(() => {
        setShareStatus(null);
      }, 3000);
    } catch (err) {
      console.error('Failed to share with community:', err);
      setErrorMsg(err?.response?.data?.error || 'Failed to share. Make sure the backend is running.');
      setShareStatus('error');
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        {/* Modal */}
        <div 
          className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-2xl animate-fadeSlideIn"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-5 border-b border-[var(--border-color)]">
            <div className="flex items-center gap-2">
              <span className="text-xl">📢</span>
              <h2 className="text-lg font-bold text-[var(--text-primary)]">Share Result</h2>
            </div>
            <button 
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-[var(--bg-primary)] border border-[var(--border-color)] flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-red-500/50 transition cursor-pointer"
            >
              ✕
            </button>
          </div>

          {/* Verdict Summary */}
          <div className="p-5 border-b border-[var(--border-color)]">
            <div className={`flex items-center gap-3 p-4 rounded-xl border ${
              isFake 
                ? 'bg-red-500/10 border-red-500/30' 
                : 'bg-green-500/10 border-green-500/30'
            }`}>
              <span className="text-3xl">{verdictEmoji}</span>
              <div>
                <p className={`font-bold text-lg ${isFake ? 'text-[var(--text-error)]' : 'text-[var(--text-success)]'}`}>
                  {verdict} News
                </p>
                <p className="text-sm text-[var(--text-secondary)]">
                  {(probability * 100).toFixed(1)}% confidence • {confidenceLabel}
                </p>
              </div>
            </div>
          </div>

          {/* Social Share Buttons */}
          <div className="p-5 border-b border-[var(--border-color)]">
            <p className="text-sm font-medium text-[var(--text-secondary)] mb-3">
              Share on Social Media
            </p>
            <div className="grid grid-cols-2 gap-3">
              {socialLinks.map((link) => (
                <a
                  key={link.name}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-4 py-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] hover:border-[var(--primary-accent)] transition group"
                >
                  <span className="text-lg">{link.icon}</span>
                  <span className="text-sm font-medium text-[var(--text-primary)] group-hover:text-[var(--primary-accent)] transition">
                    {link.name}
                  </span>
                </a>
              ))}
            </div>
          </div>

          {/* Share with Community */}
          <div className="p-5">
            <p className="text-sm font-medium text-[var(--text-secondary)] mb-3">
              Share with TruthChecker Community
            </p>
            <p className="text-xs text-[var(--text-muted)] mb-4">
              Your result will appear on the Community Fact-Check page for others to see and vote on.
            </p>

            {/* Category Selector */}
            <div className="mb-4">
              <label className="text-xs text-[var(--text-secondary)] mb-1.5 block">Category</label>
              <div className="flex flex-wrap gap-2">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setCategory(cat)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition cursor-pointer ${
                      category === cat
                        ? 'bg-[var(--primary-accent)] text-white'
                        : 'bg-[var(--bg-primary)] text-[var(--text-secondary)] border border-[var(--border-color)] hover:border-[var(--primary-accent)]'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Share Button */}
            {shareStatus === 'success' ? (
              <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-green-500/10 border border-green-500/30 text-[var(--text-success)]">
                <span>✓</span>
                <span className="text-sm font-medium">Shared with community! View it on the Community page.</span>
              </div>
            ) : (
              <>
                <button
                  onClick={handleShareWithCommunity}
                  disabled={shareStatus === 'sharing'}
                  className="w-full py-3 rounded-xl bg-[var(--primary-accent)] text-white font-bold text-sm hover:brightness-110 transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer btn-primary"
                >
                  {shareStatus === 'sharing' ? (
                    <span className="flex items-center justify-center gap-2">
                      <span className="inline-block animate-spin-slow">⟳</span>
                      Sharing...
                    </span>
                  ) : (
                    <span>👥 Share with Community</span>
                  )}
                </button>
                {shareStatus === 'error' && (
                  <p className="text-xs text-[var(--text-error)] mt-2 text-center">{errorMsg}</p>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default ShareModal;
