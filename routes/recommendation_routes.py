"""
routes/recommendation_routes.py
================================
Flask API endpoints for the Recommendation System.

Endpoints:
  GET /recommendations              → current user's recommendations (backward compat)
  GET /recommendations/<user_id>    → recommendations for a specific user (JSON)
  POST /recommendations/retrain     → retrain the ML model (admin only)
  POST /recommendations/log         → log a user interaction

FUTURE SCOPE:
  - WebSocket push for real-time recommendation updates
  - Pagination support for large recommendation lists
  - A/B testing endpoint for different algorithms
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.recommendation import get_recommended_users, get_rule_based_recommendations
import logging

logger = logging.getLogger(__name__)

recommendation_bp = Blueprint('recommendation', __name__)


@recommendation_bp.route('/recommendations')
@login_required
def recommendations():
    """
    API endpoint to fetch top 5 recommended connections for the current user.
    Returns JSON array of recommendation objects.
    """
    if current_user.role not in ['student', 'alumni']:
        return jsonify([])

    try:
        recs = get_recommended_users(current_user)
        return jsonify(recs)
    except Exception as e:
        logger.error(f"Error in /recommendations: {e}")
        return jsonify([])


@recommendation_bp.route('/recommendations/<int:user_id>')
@login_required
def recommendations_for_user(user_id):
    """
    API endpoint to fetch top 5 recommended connections for a specific user.

    Access control:
      - Users can fetch their own recommendations.
      - Admins can fetch recommendations for any user.

    Returns JSON:
      {
        "user_id": 1,
        "count": 5,
        "recommendations": [ { id, name, role, branch, skills, score, reason, profile_pic, source }, ... ]
      }
    """
    # Access control
    if current_user.id != user_id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        from services.recommendation_engine import hybrid_recommendation
        recs = hybrid_recommendation(user_id, limit=5)
    except Exception as e:
        logger.warning(f"ML engine unavailable for user {user_id}, falling back: {e}")
        recs = get_rule_based_recommendations(user_id, limit=5)

    return jsonify({
        'user_id': user_id,
        'count': len(recs),
        'recommendations': recs
    })


@recommendation_bp.route('/recommendations/retrain', methods=['POST'])
@login_required
def retrain_model():
    """
    Retrain the ML recommendation model.
    Admin-only endpoint.
    """
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized — admin only'}), 403

    try:
        from services.recommendation_engine import train_knn_model
        success = train_knn_model(force=True)
        if success:
            return jsonify({'status': 'success', 'message': 'Model retrained successfully'})
        else:
            return jsonify({'status': 'warning', 'message': 'Not enough data to train model'}), 200
    except Exception as e:
        logger.error(f"Retrain error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@recommendation_bp.route('/recommendations/log', methods=['POST'])
@login_required
def log_user_interaction():
    """
    Log a user interaction for the ML recommendation engine.

    POST JSON body:
      {
        "target_user_id": 5,
        "interaction_type": "profile_view"  // profile_view, job_click, mentorship_request, message, connection_request
      }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    target_user_id = data.get('target_user_id')
    interaction_type = data.get('interaction_type')

    valid_types = ['profile_view', 'job_click', 'mentorship_request', 'message', 'connection_request']
    if not target_user_id or interaction_type not in valid_types:
        return jsonify({'error': 'Invalid target_user_id or interaction_type'}), 400

    try:
        from services.recommendation_engine import log_interaction
        log_interaction(current_user.id, target_user_id, interaction_type)
        return jsonify({'status': 'logged'})
    except Exception as e:
        logger.error(f"Interaction log error: {e}")
        return jsonify({'status': 'ok'})  # non-critical, don't break UI
