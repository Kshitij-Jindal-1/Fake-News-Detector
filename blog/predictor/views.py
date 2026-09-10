"""
API views for fake news prediction.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings as django_settings

from .utils import get_predictor
from .scraper import extract_article_text, is_valid_url
from .source_verifier import verify_with_sources, combine_scores
from .feedback_store import get_feedback_store


class PredictTextView(APIView):
    """
    POST /api/predict/
    
    Analyze text and predict if it's fake or true news.
    Uses ML model + source verification for hybrid prediction.
    """
    
    def post(self, request):
        text = request.data.get('text', '')
        
        if not text or not text.strip():
            return Response(
                {'error': 'No text provided. Please include "text" in the request body.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Step 1: Check feedback history for similar articles
            feedback = get_feedback_store()
            history_signal = feedback.get_history_signal(text)
            
            # Step 2: ML Prediction
            predictor = get_predictor()
            ml_result = predictor.predict(text)
            
            if 'error' in ml_result:
                return Response(ml_result, status=status.HTTP_400_BAD_REQUEST)
            
            ml_probability = ml_result.get('probability', 0.5)
            word_count = ml_result.get('word_count', len(text.split()))
            
            # Step 3: Source Verification (if enabled)
            source_verification_enabled = getattr(django_settings, 'SOURCE_VERIFICATION_ENABLED', True)
            
            if source_verification_enabled:
                verification = verify_with_sources(text)
                source_score = verification.get('source_score', 0.5)
                search_insufficient = verification.get('search_insufficient', False)
                trusted_count = verification.get('trusted_count', 0)
                content_relevance = verification.get('signal_relevance', 0.5)
                
                # Step 4: Combine scores (ML + Source + History)
                combined = combine_scores(ml_probability, source_score, history_signal, search_insufficient, trusted_count, content_relevance, word_count=word_count)
                
                result = {
                    'prediction': 'True' if combined['combined_probability'] > 0.5 else 'Fake',
                    'probability': combined['combined_probability'],
                    'trueness_probability': combined['trueness_probability'],
                    'confidence_level': combined['confidence_level'],
                    'confidence_label': combined['confidence_label'],
                    'text_length': len(text),
                    'model_type': ml_result.get('model_type', 'DistilBERT'),
                    # Source verification details
                    'ml_score': combined['ml_score'],
                    'source_score': combined['source_score'],
                    'ml_weight': combined['ml_weight'],
                    'source_weight': combined['source_weight'],
                    'trusted_count': verification.get('trusted_count', 0),
                    'trusted_sources': verification.get('trusted_sources', []),
                    'total_results': verification.get('total_results', 0),
                    'search_queries': verification.get('search_queries', []),
                    'signal_coverage': verification.get('signal_coverage', 0),
                    'signal_trust_ratio': verification.get('signal_trust_ratio', 0),
                    'signal_relevance': verification.get('signal_relevance', 0),
                    # Feedback learning
                    'history_applied': combined.get('history_applied', False),
                    'similar_count': history_signal.get('similar_count', 0),
                    'db_total': feedback.get_total_count(),
                    'verification_enabled': True,
                    'search_insufficient': combined.get('search_insufficient', False),
                }
                
                # Step 5: Store this prediction for future learning
                prediction_id = feedback.store_prediction(
                    text=text,
                    ml_score=ml_probability,
                    source_score=source_score,
                    combined_score=combined['combined_probability'],
                    verdict=result['prediction'],
                    trusted_count=verification.get('trusted_count', 0),
                    total_results=verification.get('total_results', 0),
                )
                result['prediction_id'] = prediction_id
            else:
                # ML-only mode
                result = {
                    **ml_result,
                    'verification_enabled': False,
                }
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Prediction failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PredictURLView(APIView):
    """
    POST /api/predict/url/
    
    Scrape content from a URL and predict if it's fake or true news.
    Uses ML model + source verification for hybrid prediction.
    """
    
    def post(self, request):
        url = request.data.get('url', '')
        
        if not url or not url.strip():
            return Response(
                {'error': 'No URL provided. Please include "url" in the request body.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not is_valid_url(url):
            return Response(
                {'error': 'Invalid URL format. Please provide a valid HTTP/HTTPS URL.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Extract article content
            extraction = extract_article_text(url)
            
            if 'error' in extraction:
                return Response(extraction, status=status.HTTP_400_BAD_REQUEST)
            
            text = extraction.get('text', '')
            
            # Check feedback history
            feedback = get_feedback_store()
            history_signal = feedback.get_history_signal(text)
            
            # ML Prediction
            predictor = get_predictor()
            ml_result = predictor.predict(text)
            
            if 'error' in ml_result:
                return Response(ml_result, status=status.HTTP_400_BAD_REQUEST)
            
            ml_probability = ml_result.get('probability', 0.5)
            word_count = ml_result.get('word_count', len(text.split()))
            
            # Source Verification
            source_verification_enabled = getattr(django_settings, 'SOURCE_VERIFICATION_ENABLED', True)
            
            if source_verification_enabled:
                verification = verify_with_sources(text, source_url=url)
                source_score = verification.get('source_score', 0.5)
                search_insufficient = verification.get('search_insufficient', False)
                trusted_count = verification.get('trusted_count', 0)
                content_relevance = verification.get('signal_relevance', 0.5)
                combined = combine_scores(ml_probability, source_score, history_signal, search_insufficient, trusted_count, content_relevance, word_count=word_count)
                
                result = {
                    'prediction': 'True' if combined['combined_probability'] > 0.5 else 'Fake',
                    'probability': combined['combined_probability'],
                    'trueness_probability': combined['trueness_probability'],
                    'confidence_level': combined['confidence_level'],
                    'confidence_label': combined['confidence_label'],
                    'text_length': len(text),
                    'model_type': ml_result.get('model_type', 'DistilBERT'),
                    'ml_score': combined['ml_score'],
                    'source_score': combined['source_score'],
                    'ml_weight': combined['ml_weight'],
                    'source_weight': combined['source_weight'],
                    'trusted_count': verification.get('trusted_count', 0),
                    'trusted_sources': verification.get('trusted_sources', []),
                    'total_results': verification.get('total_results', 0),
                    'search_queries': verification.get('search_queries', []),
                    'signal_coverage': verification.get('signal_coverage', 0),
                    'signal_trust_ratio': verification.get('signal_trust_ratio', 0),
                    'signal_relevance': verification.get('signal_relevance', 0),
                    'history_applied': combined.get('history_applied', False),
                    'similar_count': history_signal.get('similar_count', 0),
                    'db_total': feedback.get_total_count(),
                    'verification_enabled': True,
                    'search_insufficient': combined.get('search_insufficient', False),
                }
                
                # Store for future learning
                prediction_id = feedback.store_prediction(
                    text=text,
                    ml_score=ml_probability,
                    source_score=source_score,
                    combined_score=combined['combined_probability'],
                    verdict=result['prediction'],
                    trusted_count=verification.get('trusted_count', 0),
                    total_results=verification.get('total_results', 0),
                )
                result['prediction_id'] = prediction_id
            else:
                result = {**ml_result, 'verification_enabled': False}
            
            # Add extraction metadata
            result['source'] = extraction.get('source', url)
            if 'title' in extraction:
                result['title'] = extraction['title']
            if 'author' in extraction:
                result['author'] = extraction['author']
            if 'date' in extraction:
                result['date'] = extraction['date']
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'URL analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthCheckView(APIView):
    """
    GET /api/health/
    
    Health check endpoint for monitoring.
    """
    
    def get(self, request):
        try:
            # Try to get the predictor to verify model is loaded
            get_predictor()
            return Response({
                'status': 'healthy',
                'model_loaded': True
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'model_loaded': False,
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class NewsHeadlinesView(APIView):
    """
    GET /api/news/
    
    Fetch latest news headlines from NewsAPI.org
    
    Query params:
        country: Country code (default: us)
        category: Category (default: general)
    
    Response:
        {
            "headlines": [
                {"text": "...", "url": "...", "source": "..."},
                ...
            ]
        }
    """
    
    def get(self, request):
        from .news_api import fetch_headlines
        
        country = request.query_params.get('country', 'in')
        category = request.query_params.get('category', 'general')
        
        try:
            headlines = fetch_headlines(country=country, category=category)
            return Response({
                'headlines': headlines,
                'count': len(headlines)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': f'Failed to fetch headlines: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeedbackCorrectionView(APIView):
    """
    POST /api/feedback/correct/
    
    Allows users to correct a wrong prediction via thumbs up/down.
    This updates the stored verdict so it doesn't poison future predictions.
    
    Request body:
        {
            "prediction_id": 5,
            "correct_verdict": "True"  // or "Fake"
        }
    """
    
    def post(self, request):
        prediction_id = request.data.get('prediction_id')
        correct_verdict = request.data.get('correct_verdict')
        
        if not prediction_id or not correct_verdict:
            return Response(
                {'error': 'prediction_id and correct_verdict are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if correct_verdict not in ('True', 'Fake'):
            return Response(
                {'error': 'correct_verdict must be "True" or "Fake"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        feedback = get_feedback_store()
        success = feedback.correct_prediction(int(prediction_id), correct_verdict)
        
        if success:
            return Response({
                'message': f'Prediction #{prediction_id} corrected to {correct_verdict}',
                'new_verdict': correct_verdict,
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': f'Prediction #{prediction_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class FeedbackClearView(APIView):
    """
    DELETE /api/feedback/clear/
    
    Deletes ALL stored predictions for a fresh start.
    """
    
    def delete(self, request):
        feedback = get_feedback_store()
        count = feedback.delete_all()
        return Response({
            'message': f'Deleted {count} predictions. Database is now empty.',
            'deleted_count': count,
        }, status=status.HTTP_200_OK)


# ============================================================================
# COMMUNITY FACT-CHECKER VIEWS
# ============================================================================

class CommunityListView(APIView):
    """
    GET /api/community/
    
    List community fact-check posts with search, filter, sort, pagination.
    
    Query params:
        search: Search text in title/preview
        category: Filter by category (empty = all)
        sort: 'recent' | 'top' | 'controversial'
        page: Page number (default: 1)
    """
    
    def get(self, request):
        from .community_store import get_community_store
        
        store = get_community_store()
        
        search = request.query_params.get('search', '')
        category = request.query_params.get('category', '')
        sort_by = request.query_params.get('sort', 'recent')
        page = int(request.query_params.get('page', 1))
        
        result = store.get_posts(
            search=search,
            category=category,
            sort=sort_by,
            page=page,
        )
        
        # Also include community stats
        stats = store.get_stats()
        result['stats'] = stats
        
        return Response(result, status=status.HTTP_200_OK)


class CommunityCreateView(APIView):
    """
    POST /api/community/create/
    
    Share a prediction result with the community.
    
    Request body:
        {
            "title": "...",
            "text": "...",
            "verdict": "True" or "Fake",
            "probability": 0.85,
            "confidence_label": "High",
            "source_url": "https://...",
            "category": "Health",
            "ml_score": 0.9,
            "source_score": 0.8,
            "trusted_count": 3,
            "total_results": 10
        }
    """
    
    def post(self, request):
        from .community_store import get_community_store
        
        text = request.data.get('text', '')
        verdict = request.data.get('verdict', '')
        
        if not text or not text.strip():
            return Response(
                {'error': 'Text is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if verdict not in ('True', 'Fake'):
            return Response(
                {'error': 'Verdict must be "True" or "Fake".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        store = get_community_store()
        
        post_id = store.create_post(
            title=request.data.get('title', ''),
            text=text,
            verdict=verdict,
            probability=float(request.data.get('probability', 0.5)),
            confidence_label=request.data.get('confidence_label', ''),
            source_url=request.data.get('source_url', ''),
            category=request.data.get('category', 'General'),
            ml_score=float(request.data.get('ml_score', 0.5)),
            source_score=float(request.data.get('source_score', 0.5)),
            trusted_count=int(request.data.get('trusted_count', 0)),
            total_results=int(request.data.get('total_results', 0)),
        )
        
        post = store.get_post(post_id)
        
        return Response({
            'message': 'Shared with community successfully!',
            'post': post,
        }, status=status.HTTP_201_CREATED)


class CommunityVoteView(APIView):
    """
    POST /api/community/<post_id>/vote/
    
    Vote on a community post.
    
    Request body:
        {"vote": "up"} or {"vote": "down"}
    """
    
    def post(self, request, post_id):
        from .community_store import get_community_store
        
        vote_type = request.data.get('vote', '')
        
        if vote_type not in ('up', 'down'):
            return Response(
                {'error': 'Vote must be "up" or "down".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        store = get_community_store()
        result = store.vote(post_id, vote_type)
        
        if result is None:
            return Response(
                {'error': f'Post #{post_id} not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(result, status=status.HTTP_200_OK)

