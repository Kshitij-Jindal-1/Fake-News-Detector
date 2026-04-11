/**
 * Centralized API service using axios.
 * All backend API calls go through here.
 */
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60s — source verification can be slow
});

/**
 * Analyze text for fake news detection.
 * @param {string} text - The news article text
 * @returns {Promise<object>} Prediction result
 */
export const predictText = async (text) => {
  const { data } = await apiClient.post('/predict/', { text });
  return data;
};

/**
 * Analyze a URL for fake news detection.
 * @param {string} url - The news article URL
 * @returns {Promise<object>} Prediction result
 */
export const predictUrl = async (url) => {
  const { data } = await apiClient.post('/predict/url/', { url });
  return data;
};

/**
 * Correct a prediction's verdict (user feedback).
 * @param {number} predictionId - DB prediction ID
 * @param {string} correctVerdict - 'True' or 'Fake'
 */
export const correctFeedback = async (predictionId, correctVerdict) => {
  const { data } = await apiClient.post('/feedback/correct/', {
    prediction_id: predictionId,
    correct_verdict: correctVerdict,
  });
  return data;
};

/**
 * Clear all stored predictions for a fresh start.
 */
export const clearFeedback = async () => {
  const { data } = await apiClient.delete('/feedback/clear/');
  return data;
};

// ============================================
// COMMUNITY FACT-CHECKER API
// ============================================

/**
 * Fetch community posts with filtering, sorting, pagination.
 * @param {Object} params - { search, category, sort, page }
 * @returns {Promise<object>} Paginated posts with stats
 */
export const fetchCommunityPosts = async (params = {}) => {
  const { data } = await apiClient.get('/community/', { params });
  return data;
};

/**
 * Share a prediction result with the community.
 * @param {Object} postData - Post data from prediction result
 * @returns {Promise<object>} Created post
 */
export const createCommunityPost = async (postData) => {
  const { data } = await apiClient.post('/community/create/', postData);
  return data;
};

/**
 * Vote on a community post.
 * @param {number} postId - Community post ID
 * @param {string} voteType - 'up' or 'down'
 * @returns {Promise<object>} Updated vote counts
 */
export const voteCommunityPost = async (postId, voteType) => {
  const { data } = await apiClient.post(`/community/${postId}/vote/`, { vote: voteType });
  return data;
};

export default apiClient;
