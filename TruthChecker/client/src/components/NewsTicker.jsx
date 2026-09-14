import React, { useState, useEffect, useRef } from 'react';

/**
 * NewsTicker Component
 * 
 * Displays smooth infinite scrolling news headlines fetched from Google News RSS.
 * Uses CSS animation with duplicated content for seamless looping.
 */
const NewsTicker = () => {
  const [headlines, setHeadlines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const tickerRef = useRef(null);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const apiBase = import.meta.env.VITE_API_URL || 'https://fake-news-detector-production-66f7.up.railway.app/api';
        const response = await fetch(`${apiBase}/news/?country=in&category=general`);
        
        if (response.ok) {
          const data = await response.json();
          if (data.headlines && data.headlines.length > 0) {
            let fetchedHeadlines = data.headlines;
            // Pad headlines to ensure smooth infinite scroll even on wide screens
            // Need enough items to definitely exceed viewport width
            const MIN_ITEMS = 10;
            while (fetchedHeadlines.length < MIN_ITEMS && fetchedHeadlines.length > 0) {
              fetchedHeadlines = [...fetchedHeadlines, ...fetchedHeadlines];
            }
            setHeadlines(fetchedHeadlines);
          }
        }
      } catch (error) {
        console.log('News ticker fetch failed:', error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
    
    // Refresh every 10 minutes
    const interval = setInterval(fetchNews, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Don't render if no headlines
  if (loading || headlines.length === 0) {
    return (
      <div className="news-ticker-bar">
        <div className="news-ticker-label">LATEST NEWS</div>
        <span className="news-ticker-loading">
          {loading ? 'Loading headlines...' : 'No headlines available'}
        </span>
      </div>
    );
  }

  // Calculate animation duration based on content length (more headlines = slower)
  const duration = Math.max(30, headlines.length * 4);

  return (
    <div 
      className="news-ticker-bar"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      {/* Label */}
      <div className="news-ticker-label">
        LATEST NEWS
      </div>
      
      {/* Scrolling container */}
      <div className="news-ticker-track">
        <div 
          ref={tickerRef}
          className="news-ticker-content"
          style={{
            animationDuration: `${duration}s`,
            animationPlayState: isPaused ? 'paused' : 'running',
          }}
        >
          {/* First set */}
          {headlines.map((headline, index) => (
            <a 
              key={index}
              href={headline.url}
              target="_blank"
              rel="noopener noreferrer"
              className="news-ticker-item"
              title={`Source: ${headline.source}`}
            >
              <span className="news-ticker-text">{headline.text}</span>
              {headline.source && (
                <span className="news-ticker-source">{headline.source}</span>
              )}
            </a>
          ))}
          {/* Duplicate for seamless infinite loop */}
          {headlines.map((headline, index) => (
            <a 
              key={`dup-${index}`}
              href={headline.url}
              target="_blank"
              rel="noopener noreferrer"
              className="news-ticker-item"
              title={`Source: ${headline.source}`}
            >
              <span className="news-ticker-text">{headline.text}</span>
              {headline.source && (
                <span className="news-ticker-source">{headline.source}</span>
              )}
            </a>
          ))}
        </div>
      </div>
    </div>
  );
};

export default NewsTicker;
