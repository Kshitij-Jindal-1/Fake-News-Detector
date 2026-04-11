"""
Community Fact-Checker Store.

SQLite-backed storage for community-shared predictions.
Users can share their AI prediction results, and others can vote on them.

Tables:
  - community_posts: shared predictions with title, verdict, scores, votes
"""

import os
import sqlite3
import math
from datetime import datetime
from typing import Dict, List, Optional


class CommunityStore:
    """
    Manages community fact-check posts in a local SQLite database.
    
    Posts are created when users share their prediction results.
    Other users can upvote/downvote posts.
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, 'community.db')
        
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS community_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    text_preview TEXT NOT NULL,
                    full_text TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    probability REAL NOT NULL,
                    confidence_label TEXT DEFAULT '',
                    source_url TEXT DEFAULT '',
                    category TEXT DEFAULT 'General',
                    upvotes INTEGER DEFAULT 0,
                    downvotes INTEGER DEFAULT 0,
                    ml_score REAL DEFAULT 0.5,
                    source_score REAL DEFAULT 0.5,
                    trusted_count INTEGER DEFAULT 0,
                    total_results INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_community_created 
                ON community_posts(created_at DESC)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_community_category 
                ON community_posts(category)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_community_votes 
                ON community_posts(upvotes DESC)
            ''')
            conn.commit()
        print(f"[COMMUNITY] Database initialized at {self.db_path}")

    def create_post(
        self,
        title: str,
        text: str,
        verdict: str,
        probability: float,
        confidence_label: str = '',
        source_url: str = '',
        category: str = 'General',
        ml_score: float = 0.5,
        source_score: float = 0.5,
        trusted_count: int = 0,
        total_results: int = 0,
    ) -> int:
        """
        Create a new community post from a prediction result.
        
        Returns the new post ID.
        """
        # Create a title from the first line/sentence if not provided
        if not title:
            title = text[:100].split('\n')[0].strip()
            if len(title) < len(text[:100]):
                title = title
            else:
                title = title + '...'

        text_preview = text[:300].replace('\n', ' ').strip()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO community_posts 
                (title, text_preview, full_text, verdict, probability,
                 confidence_label, source_url, category,
                 ml_score, source_score, trusted_count, total_results,
                 created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title,
                text_preview,
                text[:2000],  # Limit stored text
                verdict,
                probability,
                confidence_label,
                source_url,
                category,
                ml_score,
                source_score,
                trusted_count,
                total_results,
                datetime.now().isoformat(),
            ))
            conn.commit()
            post_id = cursor.lastrowid

        print(f"[COMMUNITY] Created post #{post_id}: '{title[:50]}' ({verdict})")
        return post_id

    def get_posts(
        self,
        search: str = '',
        category: str = '',
        sort: str = 'recent',
        page: int = 1,
        page_size: int = 12,
    ) -> Dict:
        """
        Get community posts with filtering, sorting, and pagination.
        
        Args:
            search: Text search in title/text_preview
            category: Filter by category (empty = all)
            sort: 'recent', 'top', 'controversial'
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Dict with posts list, total count, page info
        """
        conditions = []
        params = []

        if search:
            conditions.append("(title LIKE ? OR text_preview LIKE ?)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        if category and category.lower() != 'all':
            conditions.append("category = ?")
            params.append(category)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Sort order
        order_map = {
            'recent': 'created_at DESC',
            'top': '(upvotes - downvotes) DESC, created_at DESC',
            'controversial': 'ABS(upvotes - downvotes) ASC, (upvotes + downvotes) DESC',
        }
        order = order_map.get(sort, 'created_at DESC')

        offset = (page - 1) * page_size

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get total count
            count_query = f"SELECT COUNT(*) FROM community_posts {where_clause}"
            total = conn.execute(count_query, params).fetchone()[0]

            # Get posts
            query = f"""
                SELECT * FROM community_posts 
                {where_clause}
                ORDER BY {order}
                LIMIT ? OFFSET ?
            """
            rows = conn.execute(query, params + [page_size, offset]).fetchall()

        posts = []
        for row in rows:
            posts.append({
                'id': row['id'],
                'title': row['title'],
                'text_preview': row['text_preview'],
                'full_text': row['full_text'],
                'verdict': row['verdict'],
                'probability': row['probability'],
                'confidence_label': row['confidence_label'],
                'source_url': row['source_url'],
                'category': row['category'],
                'upvotes': row['upvotes'],
                'downvotes': row['downvotes'],
                'ml_score': row['ml_score'],
                'source_score': row['source_score'],
                'trusted_count': row['trusted_count'],
                'total_results': row['total_results'],
                'created_at': row['created_at'],
                'net_votes': row['upvotes'] - row['downvotes'],
            })

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return {
            'posts': posts,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
        }

    def vote(self, post_id: int, vote_type: str) -> Optional[Dict]:
        """
        Vote on a community post.
        
        Args:
            post_id: The post ID
            vote_type: 'up' or 'down'
            
        Returns:
            Updated vote counts, or None if post not found
        """
        column = 'upvotes' if vote_type == 'up' else 'downvotes'

        with sqlite3.connect(self.db_path) as conn:
            # Check post exists
            row = conn.execute(
                'SELECT id FROM community_posts WHERE id = ?', (post_id,)
            ).fetchone()

            if not row:
                return None

            conn.execute(
                f'UPDATE community_posts SET {column} = {column} + 1 WHERE id = ?',
                (post_id,)
            )
            conn.commit()

            # Get updated counts
            conn.row_factory = sqlite3.Row
            updated = conn.execute(
                'SELECT upvotes, downvotes FROM community_posts WHERE id = ?',
                (post_id,)
            ).fetchone()

        return {
            'post_id': post_id,
            'upvotes': updated['upvotes'],
            'downvotes': updated['downvotes'],
            'net_votes': updated['upvotes'] - updated['downvotes'],
        }

    def get_post(self, post_id: int) -> Optional[Dict]:
        """Get a single post by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM community_posts WHERE id = ?', (post_id,)
            ).fetchone()

        if not row:
            return None

        return {
            'id': row['id'],
            'title': row['title'],
            'text_preview': row['text_preview'],
            'full_text': row['full_text'],
            'verdict': row['verdict'],
            'probability': row['probability'],
            'confidence_label': row['confidence_label'],
            'source_url': row['source_url'],
            'category': row['category'],
            'upvotes': row['upvotes'],
            'downvotes': row['downvotes'],
            'ml_score': row['ml_score'],
            'source_score': row['source_score'],
            'trusted_count': row['trusted_count'],
            'total_results': row['total_results'],
            'created_at': row['created_at'],
            'net_votes': row['upvotes'] - row['downvotes'],
        }

    def get_stats(self) -> Dict:
        """Get community statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute('SELECT COUNT(*) FROM community_posts').fetchone()[0]
            fake = conn.execute(
                "SELECT COUNT(*) FROM community_posts WHERE verdict='Fake'"
            ).fetchone()[0]
            true = conn.execute(
                "SELECT COUNT(*) FROM community_posts WHERE verdict='True'"
            ).fetchone()[0]
            total_votes = conn.execute(
                'SELECT COALESCE(SUM(upvotes + downvotes), 0) FROM community_posts'
            ).fetchone()[0]

        return {
            'total_posts': total,
            'fake_count': fake,
            'true_count': true,
            'total_votes': total_votes,
        }


# Singleton
_community_store = None

def get_community_store() -> CommunityStore:
    """Get or create the singleton CommunityStore instance."""
    global _community_store
    if _community_store is None:
        _community_store = CommunityStore()
    return _community_store
