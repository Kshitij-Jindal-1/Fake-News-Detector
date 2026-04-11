"""
Feedback Learning Store for fake news detection.

Stores every analyzed article in a local SQLite database and uses
TF-IDF cosine similarity to compare new articles against historical
predictions. This creates a self-improving knowledge base that gets
smarter with every article analyzed.

How it works:
  1. After each prediction → store(article_keywords, scores, verdict)
  2. Before each prediction → find_similar(new_article) 
  3. If similar articles exist → use their verdicts as a 4th signal
  4. More data over time → better predictions

Technical approach:
  - SQLite for persistent storage (lightweight, no server needed)
  - TF-IDF vectorization for text representation
  - Cosine similarity for comparing articles
"""

import os
import json
import sqlite3
import math
import re
from typing import List, Dict, Optional, Tuple
from collections import Counter
from datetime import datetime


# ============================================================================
# TF-IDF IMPLEMENTATION (lightweight, no external dependencies)
# ============================================================================

class TFIDFVectorizer:
    """
    Lightweight TF-IDF implementation without requiring scikit-learn.
    
    TF-IDF = Term Frequency × Inverse Document Frequency
    
    - TF: How often a word appears in THIS document
    - IDF: How rare a word is across ALL documents
    - Words that are frequent in one doc but rare overall = most important
    """

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Extract meaningful tokens from text."""
        # Lowercase and extract words (3+ chars)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'out', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why',
            'how', 'all', 'both', 'each', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'just', 'because', 'but', 'and',
            'or', 'if', 'while', 'about', 'up', 'that', 'this', 'these',
            'those', 'it', 'its', 'he', 'she', 'they', 'we', 'you',
            'said', 'also', 'which', 'who', 'whom', 'what', 'been',
            'them', 'him', 'her', 'his', 'their', 'our', 'your', 'my',
        }
        return [w for w in words if w not in stop_words]

    @staticmethod
    def compute_tf(tokens: List[str]) -> Dict[str, float]:
        """
        Term Frequency: count of each word / total words.
        Normalized so longer documents don't dominate.
        """
        count = Counter(tokens)
        total = len(tokens) if tokens else 1
        return {word: freq / total for word, freq in count.items()}

    @staticmethod
    def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """
        Cosine similarity between two TF vectors.
        
        cos(A, B) = (A · B) / (|A| × |B|)
        
        Returns 0.0 (completely different) to 1.0 (identical).
        """
        # Find common terms
        common_terms = set(vec_a.keys()) & set(vec_b.keys())
        
        if not common_terms:
            return 0.0
        
        # Dot product
        dot_product = sum(vec_a[t] * vec_b[t] for t in common_terms)
        
        # Magnitudes
        mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
        
        if mag_a == 0 or mag_b == 0:
            return 0.0
        
        return dot_product / (mag_a * mag_b)


# ============================================================================
# FEEDBACK STORE (SQLite-backed learning database)
# ============================================================================

class FeedbackStore:
    """
    Persistent store for prediction feedback that enables learning over time.
    
    Every analyzed article is stored with its scores and verdict.
    New articles are compared against the database using TF-IDF similarity
    to find previously seen similar content, whose verdicts inform the
    current prediction.
    """

    def __init__(self, db_path: str = None):
        """Initialize the store with a SQLite database."""
        if db_path is None:
            # Store in the project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, 'feedback_learning.db')
        
        self.db_path = db_path
        self.vectorizer = TFIDFVectorizer()
        self._init_db()

    def _init_db(self):
        """Create the database table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    text_preview TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    tf_vector TEXT NOT NULL,
                    ml_score REAL NOT NULL,
                    source_score REAL NOT NULL,
                    combined_score REAL NOT NULL,
                    verdict TEXT NOT NULL,
                    trusted_count INTEGER DEFAULT 0,
                    total_results INTEGER DEFAULT 0
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_verdict 
                ON predictions(verdict)
            ''')
            conn.commit()
        print(f"[FEEDBACK] Database initialized at {self.db_path}")

    def store_prediction(
        self,
        text: str,
        ml_score: float,
        source_score: float,
        combined_score: float,
        verdict: str,
        trusted_count: int = 0,
        total_results: int = 0,
    ) -> int:
        """
        Store a prediction result for future reference.
        
        Called AFTER every prediction to build the knowledge base.
        Returns the ID of the inserted row.
        """
        tokens = self.vectorizer.tokenize(text)
        tf_vector = self.vectorizer.compute_tf(tokens)
        keywords = ' '.join(set(tokens[:50]))  # Store top 50 unique keywords
        
        # Text preview (first 200 chars for display)
        preview = text[:200].replace('\n', ' ').strip()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO predictions 
                (created_at, text_preview, keywords, tf_vector, 
                 ml_score, source_score, combined_score, verdict,
                 trusted_count, total_results)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                preview,
                keywords,
                json.dumps(tf_vector),
                ml_score,
                source_score,
                combined_score,
                verdict,
                trusted_count,
                total_results,
            ))
            conn.commit()
            row_id = cursor.lastrowid
        
        count = self.get_total_count()
        print(f"[FEEDBACK] Stored prediction #{row_id} (verdict={verdict}). "
              f"Database now has {count} articles.")
        return row_id

    def find_similar(
        self, 
        text: str, 
        similarity_threshold: float = 0.3,
        max_results: int = 5,
    ) -> List[Dict]:
        """
        Find articles in the database that are similar to the input text.
        
        Uses TF-IDF cosine similarity to compare the new article's
        keyword distribution against all stored articles.
        
        Args:
            text: The new article text to compare
            similarity_threshold: Minimum similarity to consider a match (0-1)
            max_results: Maximum number of similar articles to return
            
        Returns:
            List of similar articles with their scores and similarity
        """
        # Vectorize the input text
        tokens = self.vectorizer.tokenize(text)
        input_tf = self.vectorizer.compute_tf(tokens)
        
        if not input_tf:
            return []
        
        # Fetch all stored articles
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, text_preview, tf_vector, ml_score, 
                       source_score, combined_score, verdict,
                       trusted_count, created_at
                FROM predictions
                ORDER BY created_at DESC
                LIMIT 500
            ''')
            rows = cursor.fetchall()
        
        if not rows:
            return []
        
        # Compare against each stored article
        similar = []
        for row in rows:
            stored_tf = json.loads(row[2])
            similarity = self.vectorizer.cosine_similarity(input_tf, stored_tf)
            
            if similarity >= similarity_threshold:
                similar.append({
                    'id': row[0],
                    'preview': row[1],
                    'similarity': round(similarity, 4),
                    'ml_score': row[3],
                    'source_score': row[4],
                    'combined_score': row[5],
                    'verdict': row[6],
                    'trusted_count': row[7],
                    'created_at': row[8],
                })
        
        # Sort by similarity (highest first)
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        return similar[:max_results]

    def get_history_signal(self, text: str) -> Dict:
        """
        Get a prediction signal based on historical similar articles.
        
        This is the main interface used by the prediction pipeline.
        
        Returns:
            Dictionary with:
            - history_score: 0.0-1.0 score based on similar articles
            - confidence: how confident we are in this signal
            - similar_count: number of similar articles found
            - similar_articles: list of similar articles with details
        """
        similar = self.find_similar(text)
        
        if not similar:
            return {
                'history_score': 0.5,  # Neutral — no history
                'confidence': 0.0,     # Zero confidence
                'similar_count': 0,
                'similar_articles': [],
                'has_history': False,
            }
        
        # Weighted average of similar articles' verdicts
        # Weight by similarity score (more similar = more influence)
        total_weight = 0
        weighted_score = 0
        
        for article in similar:
            weight = article['similarity']
            # Use the combined score from previous analysis
            score = article['combined_score']
            weighted_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            history_score = weighted_score / total_weight
        else:
            history_score = 0.5
        
        # Confidence is based on:
        # 1. How many similar articles we found
        # 2. How similar they are (average similarity)
        avg_similarity = sum(a['similarity'] for a in similar) / len(similar)
        count_factor = min(1.0, len(similar) / 3.0)  # 3+ articles = full confidence
        confidence = avg_similarity * count_factor
        
        print(f"[FEEDBACK] Found {len(similar)} similar articles. "
              f"History score: {history_score:.4f}, Confidence: {confidence:.4f}")
        
        return {
            'history_score': round(history_score, 4),
            'confidence': round(confidence, 4),
            'similar_count': len(similar),
            'similar_articles': similar[:3],  # Top 3 for display
            'has_history': True,
        }

    def correct_prediction(self, prediction_id: int, correct_verdict: str) -> bool:
        """
        Correct a prediction's verdict based on user feedback.
        
        When a user clicks thumbs down (wrong prediction), this flips the
        verdict and adjusts the combined score so it doesn't poison future
        predictions via the history signal.
        
        Args:
            prediction_id: The ID of the prediction to correct
            correct_verdict: The correct verdict ('True' or 'Fake')
            
        Returns:
            True if the prediction was found and corrected
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if prediction exists
                cursor = conn.execute(
                    'SELECT id, verdict, combined_score FROM predictions WHERE id = ?',
                    (prediction_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return False
                
                old_verdict = row[1]
                
                # Flip the combined_score to match the corrected verdict
                # If corrected to "True" → score should be high (0.85)
                # If corrected to "Fake" → score should be low (0.15)
                corrected_score = 0.85 if correct_verdict == 'True' else 0.15
                
                conn.execute('''
                    UPDATE predictions 
                    SET verdict = ?, combined_score = ?
                    WHERE id = ?
                ''', (correct_verdict, corrected_score, prediction_id))
                conn.commit()
                
                print(f"[FEEDBACK] Corrected prediction #{prediction_id}: "
                      f"{old_verdict} → {correct_verdict} (score → {corrected_score})")
                return True
                
        except Exception as e:
            print(f"[FEEDBACK] Error correcting prediction: {e}")
            return False

    def delete_prediction(self, prediction_id: int) -> bool:
        """Delete a single prediction by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'DELETE FROM predictions WHERE id = ?', (prediction_id,)
                )
                conn.commit()
                deleted = cursor.rowcount > 0
                if deleted:
                    print(f"[FEEDBACK] Deleted prediction #{prediction_id}")
                return deleted
        except Exception as e:
            print(f"[FEEDBACK] Error deleting prediction: {e}")
            return False

    def delete_all(self) -> int:
        """
        Delete ALL predictions for a fresh start.
        Returns the number of deleted rows.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('DELETE FROM predictions')
                count = cursor.rowcount
                conn.commit()
                print(f"[FEEDBACK] Deleted all {count} predictions. Fresh start!")
                return count
        except Exception as e:
            print(f"[FEEDBACK] Error deleting all: {e}")
            return 0

    def get_total_count(self) -> int:
        """Get total number of stored predictions."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM predictions')
            return cursor.fetchone()[0]

    def get_stats(self) -> Dict:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute('SELECT COUNT(*) FROM predictions').fetchone()[0]
            fake = conn.execute(
                "SELECT COUNT(*) FROM predictions WHERE verdict='Fake'"
            ).fetchone()[0]
            true = conn.execute(
                "SELECT COUNT(*) FROM predictions WHERE verdict='True'"
            ).fetchone()[0]
        
        return {
            'total_articles': total,
            'fake_count': fake,
            'true_count': true,
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_feedback_store = None

def get_feedback_store() -> FeedbackStore:
    """Get or create the singleton FeedbackStore instance."""
    global _feedback_store
    if _feedback_store is None:
        _feedback_store = FeedbackStore()
    return _feedback_store
