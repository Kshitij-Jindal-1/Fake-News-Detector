"""
URL configuration for predictor app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('predict/', views.PredictTextView.as_view(), name='predict_text'),
    path('predict/url/', views.PredictURLView.as_view(), name='predict_url'),
    path('health/', views.HealthCheckView.as_view(), name='health_check'),
    path('news/', views.NewsHeadlinesView.as_view(), name='news_headlines'),
    path('feedback/correct/', views.FeedbackCorrectionView.as_view(), name='feedback_correct'),
    path('feedback/clear/', views.FeedbackClearView.as_view(), name='feedback_clear'),
    # Community Fact-Checker
    path('community/', views.CommunityListView.as_view(), name='community_list'),
    path('community/create/', views.CommunityCreateView.as_view(), name='community_create'),
    path('community/<int:post_id>/vote/', views.CommunityVoteView.as_view(), name='community_vote'),
]

