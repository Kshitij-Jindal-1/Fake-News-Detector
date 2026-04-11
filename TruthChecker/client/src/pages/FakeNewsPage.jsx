import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import NewsTicker from '../components/NewsTicker';
import Footer from '../components/Footer';
import { fetchCommunityPosts, voteCommunityPost } from '../services/api';

const CATEGORIES = ['All', 'Health', 'Technology', 'Politics', 'Finance', 'Entertainment', 'Science', 'Sports'];

const wordCount = (text) => text ? text.trim().split(/\s+/).length : 0;

/**
 * PostDetailModal - Opens when a user clicks a community post card.
 * Shows full content for short posts, preview + "Read Source" for long posts.
 */
const PostDetailModal = ({ post, onClose, onVote }) => {
  if (!post) return null;

  const isLong = wordCount(post.full_text || post.text_preview) > 100;
  const displayText = post.full_text || post.text_preview;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl animate-fadeSlideIn"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Verdict Stripe */}
        <div className={`h-2 w-full rounded-t-2xl ${post.verdict === 'Fake' ? 'bg-red-500' : 'bg-green-500'}`}></div>

        {/* Header */}
        <div className="flex items-start justify-between p-6 pb-0">
          <div className="flex items-center gap-3 flex-1">
            <span className={`px-3 py-1 rounded-lg text-sm font-bold ${
              post.verdict === 'Fake'
                ? 'bg-red-500/15 text-[var(--text-error)] border border-red-500/30'
                : 'bg-green-500/15 text-[var(--text-success)] border border-green-500/30'
            }`}>
              {post.verdict === 'Fake' ? '🚨 FAKE' : '✅ TRUE'}
            </span>
            <span className="px-2.5 py-1 rounded-md bg-[var(--bg-deep)] border border-[var(--border-color)] text-xs text-[var(--text-secondary)]">
              {post.category}
            </span>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-[var(--bg-primary)] border border-[var(--border-color)] flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-red-500/50 transition cursor-pointer flex-shrink-0"
          >
            ✕
          </button>
        </div>

        {/* Title */}
        <div className="px-6 pt-4">
          <h2 className="text-xl font-bold text-[var(--text-primary)] leading-tight">
            {post.title}
          </h2>
          <div className="flex items-center gap-3 mt-2 text-xs text-[var(--text-muted)]">
            <span>📅 {new Date(post.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
            <span>•</span>
            <span>{(post.probability * 100).toFixed(0)}% AI confidence</span>
            {post.confidence_label && (
              <>
                <span>•</span>
                <span>{post.confidence_label}</span>
              </>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          {isLong ? (
            <>
              {/* Long post: show truncated preview */}
              <div className="bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-xl p-4 mb-4 max-h-[250px] overflow-y-auto">
                <p className="text-[var(--text-primary)] text-sm whitespace-pre-wrap leading-relaxed">
                  {displayText.substring(0, 500)}...
                </p>
                <p className="text-xs text-[var(--text-muted)] mt-3 italic">
                  📄 Full article is {wordCount(displayText)} words — read at source for complete text.
                </p>
              </div>
              {post.source_url && (
                <a
                  href={post.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-bold text-sm hover:brightness-110 transition"
                >
                  🔗 Read Full Article at Source
                </a>
              )}
            </>
          ) : (
            <>
              {/* Short post: show full content */}
              <div className="bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-xl p-4 max-h-[250px] overflow-y-auto">
                <p className="text-[var(--text-primary)] text-sm whitespace-pre-wrap leading-relaxed">
                  {displayText}
                </p>
              </div>
              {post.source_url && (
                <a
                  href={post.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-[var(--text-info)] hover:underline mt-3 inline-flex items-center gap-1"
                >
                  🔗 View original source
                </a>
              )}
            </>
          )}
        </div>

        {/* AI Analysis Summary */}
        <div className="px-6 pb-4">
          <div className="grid grid-cols-3 gap-3">
            {(() => {
              const mlPct = (post.ml_score * 100).toFixed(0);
              const srcPct = (post.source_score * 100).toFixed(0);
              const trustRatio = post.total_results > 0 ? post.trusted_count / post.total_results : 0;
              const isFakeVerdict = post.verdict === 'Fake';
              // Color: green if score supports verdict, red if contradicts
              const mlColor = (isFakeVerdict ? post.ml_score < 0.5 : post.ml_score >= 0.5) ? 'text-green-500' : 'text-red-400';
              const srcColor = (isFakeVerdict ? post.source_score < 0.5 : post.source_score >= 0.5) ? 'text-green-500' : 'text-red-400';
              const trustColor = trustRatio < 0.3 ? 'text-red-400' : trustRatio < 0.6 ? 'text-yellow-400' : 'text-green-500';
              const trustLabel = trustRatio < 0.3 ? 'Low credibility' : trustRatio < 0.6 ? 'Mixed signals' : 'Well sourced';
              return (
                <>
                  <div className="bg-[var(--bg-deep)] p-3 rounded-lg border border-[var(--border-color)] text-center">
                    <p className="text-xs text-[var(--text-muted)]">ML Score</p>
                    <p className={`text-lg font-bold ${mlColor}`}>{mlPct}%</p>
                  </div>
                  <div className="bg-[var(--bg-deep)] p-3 rounded-lg border border-[var(--border-color)] text-center">
                    <p className="text-xs text-[var(--text-muted)]">Source Score</p>
                    <p className={`text-lg font-bold ${srcColor}`}>{srcPct}%</p>
                  </div>
                  <div className="bg-[var(--bg-deep)] p-3 rounded-lg border border-[var(--border-color)] text-center">
                    <p className="text-xs text-[var(--text-muted)]">Related Sources</p>
                    <p className={`text-lg font-bold ${trustColor}`}>{post.trusted_count}/{post.total_results}</p>
                    <p className={`text-[10px] mt-0.5 ${trustColor}`}>{trustLabel}</p>
                  </div>
                </>
              );
            })()}
          </div>
        </div>

        {/* Vote + Actions Footer */}
        <div className="px-6 pb-6 flex items-center justify-between border-t border-[var(--border-color)] pt-4">
          <div className="flex items-center gap-1 bg-[var(--bg-deep)] rounded-lg p-1 border border-[var(--border-color)]">
            <button
              onClick={() => onVote(post.id, 'up')}
              className="px-3 py-1.5 hover:bg-green-500/10 hover:text-green-500 rounded transition text-[var(--text-secondary)] cursor-pointer"
            >
              ▲ Agree
            </button>
            <span className={`mx-2 text-sm font-mono font-medium ${
              post.net_votes > 0 ? 'text-green-500' : post.net_votes < 0 ? 'text-red-500' : 'text-[var(--text-muted)]'
            }`}>
              {post.net_votes}
            </span>
            <button
              onClick={() => onVote(post.id, 'down')}
              className="px-3 py-1.5 hover:bg-red-500/10 hover:text-red-500 rounded transition text-[var(--text-secondary)] cursor-pointer"
            >
              ▼ Disagree
            </button>
          </div>

          {/* Social Share */}
          <div className="flex items-center gap-2">
            <a
              href={`https://wa.me/?text=${encodeURIComponent(`Check this fact-check: "${post.title}" — Verdict: ${post.verdict}`)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="w-8 h-8 rounded-full bg-[var(--bg-primary)] border border-[var(--border-color)] flex items-center justify-center text-sm hover:border-green-500 transition"
              title="Share on WhatsApp"
            >
              💬
            </a>
            <a
              href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(`${post.verdict === 'Fake' ? '🚨' : '✅'} "${post.title}" — AI says ${post.verdict} (${(post.probability * 100).toFixed(0)}% confidence)`)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="w-8 h-8 rounded-full bg-[var(--bg-primary)] border border-[var(--border-color)] flex items-center justify-center text-sm hover:border-blue-500 transition"
              title="Share on X"
            >
              𝕏
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Community Page - Shows user-submitted fact checks with voting
 */
const FakeNewsPage = () => {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');
  const [sort, setSort] = useState('recent');
  const [page, setPage] = useState(1);
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedPost, setSelectedPost] = useState(null);

  const queryClient = useQueryClient();

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 500);
    return () => clearTimeout(timer);
  }, [search]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, category, sort]);

  // Fetch posts
  const { data, isLoading, isError } = useQuery({
    queryKey: ['communityPosts', { search: debouncedSearch, category, sort, page }],
    queryFn: () => fetchCommunityPosts({
      search: debouncedSearch,
      category: category === 'All' ? '' : category,
      sort,
      page
    }),
    keepPreviousData: true,
  });

  // Vote mutation
  const voteMutation = useMutation({
    mutationFn: ({ postId, type }) => voteCommunityPost(postId, type),
    onSuccess: (updatedPost) => {
      queryClient.setQueryData(
        ['communityPosts', { search: debouncedSearch, category, sort, page }],
        (oldData) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            posts: oldData.posts.map((post) =>
              post.id === updatedPost.post_id
                ? { ...post, upvotes: updatedPost.upvotes, downvotes: updatedPost.downvotes, net_votes: updatedPost.net_votes }
                : post
            ),
          };
        }
      );
      // Also update selected post if open
      if (selectedPost && selectedPost.id === updatedPost.post_id) {
        setSelectedPost(prev => ({
          ...prev,
          upvotes: updatedPost.upvotes,
          downvotes: updatedPost.downvotes,
          net_votes: updatedPost.net_votes,
        }));
      }
    },
  });

  const handleVote = (postId, type) => {
    voteMutation.mutate({ postId, type });
  };

  const handleCardVote = (e, postId, type) => {
    e.stopPropagation();
    handleVote(postId, type);
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <NewsTicker />

      {/* Header */}
      <div className="px-4 md:px-8 lg:px-16 py-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Link to="/" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-sm">Home</Link>
                <span className="text-gray-600">/</span>
                <span className="text-[var(--primary-accent)] text-sm">Community Fact-Checker</span>
              </div>
              <h1 className="text-3xl md:text-4xl font-bold text-[var(--text-primary)]">
                👥 Community <span className="text-[var(--primary-accent)]">Fact-Checker</span>
              </h1>
              <p className="text-[var(--text-secondary)] mt-2">
                Crowdsourced fact predictions verified by AI and the community.
              </p>
            </div>

            {/* Stats */}
            {data?.stats && (
              <div className="flex gap-4 p-4 bg-[var(--bg-deep)] rounded-xl border border-[var(--border-color)]">
                <div className="text-center">
                  <p className="text-xl font-bold text-[var(--text-primary)]">{data.stats.total_posts}</p>
                  <p className="text-xs text-[var(--text-secondary)]">Fact Checks</p>
                </div>
                <div className="w-px bg-[var(--border-color)]"></div>
                <div className="text-center">
                  <p className="text-xl font-bold text-[var(--text-success)]">{data.stats.true_count}</p>
                  <p className="text-xs text-[var(--text-secondary)]">True</p>
                </div>
                <div className="w-px bg-[var(--border-color)]"></div>
                <div className="text-center">
                  <p className="text-xl font-bold text-[var(--text-error)]">{data.stats.fake_count}</p>
                  <p className="text-xs text-[var(--text-secondary)]">Fake</p>
                </div>
              </div>
            )}
          </div>

          {/* Filters & Search */}
          <div className="bg-[var(--glass-bg)] border border-[var(--glass-border)] rounded-2xl p-4 mb-8 backdrop-blur-md sticky top-20 z-10 shadow-lg">
            <div className="flex flex-col md:flex-row gap-4 justify-between">
              <div className="relative flex-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]">🔍</span>
                <input
                  type="text"
                  placeholder="Search claims or headlines..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-color)] text-[var(--text-primary)] focus:ring-2 focus:ring-[var(--primary-accent)] outline-none transition"
                />
              </div>
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value)}
                className="px-4 py-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-color)] text-[var(--text-primary)] outline-none cursor-pointer hover:border-[var(--primary-accent)] transition"
              >
                <option value="recent">🕒 Recent</option>
                <option value="top">🔥 Top Voted</option>
                <option value="controversial">⚡ Controversial</option>
              </select>
            </div>
            <div className="flex gap-2 overflow-x-auto mt-4 pb-1 no-scrollbar">
              {CATEGORIES.map(cat => (
                <button
                  key={cat}
                  onClick={() => setCategory(cat)}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition border ${
                    category === cat
                      ? 'bg-[var(--primary-accent)] text-white border-[var(--primary-accent)]'
                      : 'bg-[var(--bg-primary)] text-[var(--text-secondary)] border-[var(--border-color)] hover:border-[var(--text-secondary)]'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Content */}
          {isLoading ? (
            <div className="flex justify-center py-20">
              <div className="w-10 h-10 border-4 border-[var(--primary-accent)] border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : isError ? (
            <div className="text-center py-20 text-[var(--text-error)]">
              Failed to load community posts. Please try again.
            </div>
          ) : data?.posts.length === 0 ? (
            <div className="text-center py-20 bg-[var(--bg-secondary)] rounded-2xl border border-[var(--border-color)] border-dashed">
              <span className="text-4xl block mb-2">📭</span>
              <h3 className="text-xl font-bold text-[var(--text-primary)]">No posts found</h3>
              <p className="text-[var(--text-secondary)] mt-2">
                Be the first to analyze news and share it with the community!
              </p>
              <Link to="/" className="inline-block mt-4 px-6 py-2 bg-[var(--primary-accent)] text-white rounded-xl hover:brightness-110 transition">
                Go to Analyzer
              </Link>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {data.posts.map((post) => {
                  const isShort = wordCount(post.full_text || post.text_preview) <= 100;
                  // Check if title and preview are basically the same (short submission)
                  const titleTrimmed = post.title?.replace(/\.{3}$/, '').trim().toLowerCase() || '';
                  const previewTrimmed = post.text_preview?.replace(/\.{3}$/, '').trim().toLowerCase() || '';
                  const isTinySubmission = titleTrimmed === previewTrimmed || previewTrimmed.startsWith(titleTrimmed) && titleTrimmed.length > previewTrimmed.length * 0.8;
                  
                  return (
                    <article
                      key={post.id}
                      onClick={() => setSelectedPost(post)}
                      className="bg-[var(--bg-secondary)] rounded-xl border border-[var(--border-color)] hover:border-[var(--primary-accent)] transition duration-300 flex flex-col h-full group relative overflow-hidden cursor-pointer"
                    >
                      {/* Verdict Stripe */}
                      <div className={`h-1.5 w-full ${post.verdict === 'Fake' ? 'bg-red-500' : 'bg-green-500'}`}></div>

                      <div className="p-5 flex-1 flex flex-col">
                        <div className="flex justify-between items-start mb-3">
                          <span className="px-2.5 py-1 rounded-md bg-[var(--bg-deep)] border border-[var(--border-color)] text-xs text-[var(--text-secondary)]">
                            {post.category}
                          </span>
                          <span className={`px-2 py-1 rounded text-xs font-bold ${
                            post.verdict === 'Fake'
                              ? 'bg-red-500/10 text-[var(--text-error)] border border-red-500/20'
                              : 'bg-green-500/10 text-[var(--text-success)] border border-green-500/20'
                          }`}>
                            {post.verdict === 'Fake' ? '🚨 FAKE' : '✅ TRUE'}
                          </span>
                        </div>

                        <h3 className="text-lg font-bold text-[var(--text-primary)] mb-2 line-clamp-2 group-hover:text-[var(--primary-accent)] transition" title={post.title}>
                          {post.title}
                        </h3>

                        {/* Only show preview if it's different from the title */}
                        {!isTinySubmission && (
                          <p className="text-sm text-[var(--text-secondary)] mb-4 line-clamp-3">
                            {post.text_preview}...
                          </p>
                        )}

                        {/* For tiny submissions, show an expanded verdict section instead */}
                        {isTinySubmission && (
                          <div className={`flex items-center gap-3 p-3 rounded-lg mb-4 ${
                            post.verdict === 'Fake' 
                              ? 'bg-red-500/5 border border-red-500/15' 
                              : 'bg-green-500/5 border border-green-500/15'
                          }`}>
                            <span className="text-2xl">{post.verdict === 'Fake' ? '🚨' : '✅'}</span>
                            <div>
                              <p className={`text-sm font-medium ${post.verdict === 'Fake' ? 'text-[var(--text-error)]' : 'text-[var(--text-success)]'}`}>
                                AI says this claim is {post.verdict}
                              </p>
                              <div className="w-full bg-[var(--bg-deep)] h-1.5 rounded-full mt-1.5 overflow-hidden">
                                <div 
                                  className={`h-full rounded-full ${post.verdict === 'Fake' ? 'bg-red-500' : 'bg-green-500'}`}
                                  style={{ width: `${(post.probability * 100).toFixed(0)}%` }}
                                ></div>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Click hint */}
                        <p className="text-xs text-[var(--text-muted)] mb-3 opacity-0 group-hover:opacity-100 transition">
                          {isShort ? '📖 Click to read full text' : '🔗 Click to view details & source'}
                        </p>

                        <div className="mt-auto">
                          <div className="flex items-center justify-between text-xs text-[var(--text-muted)] mb-4">
                            <span>{(post.probability * 100).toFixed(0)}% confidence</span>
                            <span>{new Date(post.created_at).toLocaleDateString()}</span>
                          </div>

                          {/* Actions */}
                          <div className="flex items-center justify-between pt-4 border-t border-[var(--border-color)]">
                            <div className="flex items-center bg-[var(--bg-deep)] rounded-lg p-1 border border-[var(--border-color)]">
                              <button
                                onClick={(e) => handleCardVote(e, post.id, 'up')}
                                className="px-2 py-1 hover:bg-green-500/10 hover:text-green-500 rounded transition text-[var(--text-secondary)]"
                              >
                                ▲
                              </button>
                              <span className={`mx-2 text-sm font-mono font-medium ${
                                post.net_votes > 0 ? 'text-green-500' : post.net_votes < 0 ? 'text-red-500' : 'text-[var(--text-muted)]'
                              }`}>
                                {post.net_votes}
                              </span>
                              <button
                                onClick={(e) => handleCardVote(e, post.id, 'down')}
                                className="px-2 py-1 hover:bg-red-500/10 hover:text-red-500 rounded transition text-[var(--text-secondary)]"
                              >
                                ▼
                              </button>
                            </div>

                            {post.source_url && (
                              <a
                                href={post.source_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                className="text-xs text-[var(--text-info)] hover:underline flex items-center gap-1"
                              >
                                🔗 Source
                              </a>
                            )}
                          </div>
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>

              {/* Pagination */}
              {data.total_pages > 1 && (
                <div className="flex justify-center mt-12 gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={!data.has_prev}
                    className="px-4 py-2 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-primary)] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--bg-deep)] transition"
                  >
                    Previous
                  </button>
                  <span className="flex items-center px-4 font-mono text-[var(--text-secondary)]">
                    {data.page} / {data.total_pages}
                  </span>
                  <button
                    onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
                    disabled={!data.has_next}
                    className="px-4 py-2 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-primary)] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--bg-deep)] transition"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
      <Footer />

      {/* Detail Modal */}
      <PostDetailModal
        post={selectedPost}
        onClose={() => setSelectedPost(null)}
        onVote={handleVote}
      />
    </div>
  );
};

export default FakeNewsPage;
