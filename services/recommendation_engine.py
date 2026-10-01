"""
services/recommendation_engine.py
==================================
PHASE 2 — ML-Based Collaborative Filtering Recommendation Engine

Uses KNN with Cosine Similarity on a user-interaction matrix.

Interaction data (weighted scores):
  - Connection accepted  : weight 5
  - Connection request    : weight 3
  - Private message sent  : weight 4
  - Job application       : weight 2

The model is trained ONCE and cached in memory. It is retrained
only when explicitly requested or when the scheduler triggers it.

COLD START HANDLING:
  If a user has no interactions, the engine falls back to
  rule-based recommendations automatically.

=====================================================
FUTURE SCOPE (planned enhancements):
  - Hybrid deep learning model (GNN on user graph)
  - Real-time incremental model updates via streaming
  - Profile view / job click tracking for richer signals
  - Matrix factorization (SVD / ALS) for implicit feedback
  - A/B testing framework for recommendation quality
=====================================================
"""

import logging
import threading
import time
import numpy as np
from collections import defaultdict

from db_utils import get_db_connection

logger = logging.getLogger(__name__)

# =====================================================================
# Interaction weight constants
# =====================================================================
WEIGHT_CONNECTION = 5       # accepted connection (strong signal)
WEIGHT_CONN_REQUEST = 3     # sent a connection request
WEIGHT_MESSAGE = 4          # sent a private message
WEIGHT_JOB_APPLICATION = 2  # applied to a job posted by someone

# Minimum interactions required before ML kicks in (cold-start threshold)
MIN_INTERACTIONS = 2

# =====================================================================
# Global model cache  — trained once, reused across requests
# =====================================================================
_model_cache = {
    'knn_model': None,
    'interaction_matrix': None,
    'user_id_to_idx': {},
    'idx_to_user_id': {},
    'last_trained': 0,
    'lock': threading.Lock(),
}


# =====================================================================
# STEP 1:  Build the user-user interaction matrix from real DB data
# =====================================================================
def build_interaction_matrix():
    """
    Query the existing SQLite tables and construct a user × user
    interaction matrix with weighted scores.

    Sources (all from existing tables):
      - connections          → bidirectional, weight 5
      - connection_requests  → directional,  weight 3
      - private_messages     → directional,  weight 4
      - job_applications     → student→poster, weight 2

    Returns:
        interaction_matrix (np.ndarray)  — shape (n_users, n_users)
        user_id_to_idx     (dict)        — {user_id: matrix_index}
        idx_to_user_id     (dict)        — {matrix_index: user_id}
    """
    conn = get_db_connection()
    c = conn.cursor()

    try:
        # ----- Collect all user IDs (students + alumni only) -----
        users = c.execute(
            "SELECT id FROM users WHERE role IN ('student', 'alumni') ORDER BY id"
        ).fetchall()

        if not users:
            return np.array([]), {}, {}

        user_ids = [u['id'] for u in users]
        user_id_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
        idx_to_user_id = {idx: uid for uid, idx in user_id_to_idx.items()}
        n = len(user_ids)

        matrix = np.zeros((n, n), dtype=np.float32)

        # ----- 1. Accepted connections (weight 5, bidirectional) -----
        connections = c.execute(
            'SELECT user_id_1, user_id_2 FROM connections'
        ).fetchall()
        for row in connections:
            u1, u2 = row['user_id_1'], row['user_id_2']
            if u1 in user_id_to_idx and u2 in user_id_to_idx:
                i, j = user_id_to_idx[u1], user_id_to_idx[u2]
                matrix[i][j] += WEIGHT_CONNECTION
                matrix[j][i] += WEIGHT_CONNECTION

        # ----- 2. Connection requests (weight 3, sender → receiver) -----
        requests = c.execute(
            "SELECT sender_id, receiver_id FROM connection_requests WHERE status = 'pending'"
        ).fetchall()
        for row in requests:
            s, r = row['sender_id'], row['receiver_id']
            if s in user_id_to_idx and r in user_id_to_idx:
                matrix[user_id_to_idx[s]][user_id_to_idx[r]] += WEIGHT_CONN_REQUEST

        # ----- 3. Private messages (weight 4, sender → receiver) -----
        try:
            messages = c.execute(
                'SELECT sender_id, receiver_id FROM private_messages'
            ).fetchall()
            for row in messages:
                s, r = row['sender_id'], row['receiver_id']
                if s in user_id_to_idx and r in user_id_to_idx:
                    matrix[user_id_to_idx[s]][user_id_to_idx[r]] += WEIGHT_MESSAGE
        except Exception:
            # private_messages table may not exist yet
            logger.debug("private_messages table not found – skipping message interactions")

        # ----- 4. Job applications (weight 2, student → job poster) -----
        try:
            applications = c.execute('''
                SELECT ja.student_id, j.posted_by
                FROM job_applications ja
                JOIN jobs j ON ja.job_id = j.id
            ''').fetchall()
            for row in applications:
                s, p = row['student_id'], row['posted_by']
                if s in user_id_to_idx and p in user_id_to_idx:
                    matrix[user_id_to_idx[s]][user_id_to_idx[p]] += WEIGHT_JOB_APPLICATION
        except Exception:
            logger.debug("job_applications table not found – skipping job interactions")

        # ----- 5. User interactions table (if exists) -----
        try:
            interactions = c.execute(
                'SELECT user_id, target_user_id, interaction_type, COUNT(*) as cnt '
                'FROM user_interactions GROUP BY user_id, target_user_id, interaction_type'
            ).fetchall()
            type_weights = {
                'profile_view': 1,
                'job_click': 2,
                'mentorship_request': 4,
                'message': 4,
                'connection_request': 3,
            }
            for row in interactions:
                uid, tid = row['user_id'], row['target_user_id']
                itype = row['interaction_type']
                cnt = row['cnt']
                w = type_weights.get(itype, 1)
                if uid in user_id_to_idx and tid in user_id_to_idx:
                    matrix[user_id_to_idx[uid]][user_id_to_idx[tid]] += w * cnt
        except Exception:
            logger.debug("user_interactions table not found – skipping")

        logger.info(f"[ML] Interaction matrix built: {n} users, "
                     f"{int(np.count_nonzero(matrix))} non-zero entries")

        return matrix, user_id_to_idx, idx_to_user_id

    except Exception as e:
        logger.error(f"Error building interaction matrix: {e}")
        return np.array([]), {}, {}
    finally:
        conn.close()


# =====================================================================
# STEP 2:  Train KNN model (Cosine similarity)
# =====================================================================
def train_knn_model(force=False):
    """
    Train (or retrain) the KNN model on the interaction matrix.

    The model is stored in the global _model_cache and reused.
    Thread-safe via a lock.

    Args:
        force: If True, retrain even if a cached model exists.

    Returns:
        True if training succeeded, False otherwise.
    """
    global _model_cache

    with _model_cache['lock']:
        # Skip if recently trained (within last 5 minutes) and not forced
        if (not force and _model_cache['knn_model'] is not None
                and time.time() - _model_cache['last_trained'] < 300):
            return True

        try:
            from sklearn.neighbors import NearestNeighbors
            from sklearn.preprocessing import normalize

            logger.info("[ML] Training KNN recommendation model...")
            start = time.time()

            matrix, uid_to_idx, idx_to_uid = build_interaction_matrix()

            if matrix.size == 0 or matrix.shape[0] < 2:
                logger.warning("[ML] Not enough data to train model")
                _model_cache['interaction_matrix'] = matrix
                _model_cache['user_id_to_idx'] = uid_to_idx
                _model_cache['idx_to_user_id'] = idx_to_uid
                return False

            # Normalize rows (L2) for cosine similarity via KNN
            matrix_norm = normalize(matrix, axis=1, norm='l2')

            # n_neighbors = min(10, number_of_users - 1)
            k = min(10, matrix_norm.shape[0] - 1)
            if k < 1:
                logger.warning("[ML] Too few users for KNN")
                return False

            knn = NearestNeighbors(
                n_neighbors=k,
                metric='cosine',
                algorithm='brute'  # brute works well for moderate sizes
            )
            knn.fit(matrix_norm)

            # Cache everything
            _model_cache['knn_model'] = knn
            _model_cache['interaction_matrix'] = matrix_norm
            _model_cache['user_id_to_idx'] = uid_to_idx
            _model_cache['idx_to_user_id'] = idx_to_uid
            _model_cache['last_trained'] = time.time()

            elapsed = round(time.time() - start, 2)
            logger.info(f"[ML] KNN model trained in {elapsed}s — "
                         f"{matrix_norm.shape[0]} users, k={k}")
            return True

        except ImportError:
            logger.error("[ML] scikit-learn not installed. "
                         "Run: pip install scikit-learn numpy")
            return False
        except Exception as e:
            logger.error(f"[ML] Training failed: {e}")
            return False


# =====================================================================
# STEP 3:  Get ML-based recommendations for a user
# =====================================================================
def get_ml_recommendations(user_id, limit=5):
    """
    Use the trained KNN model to find the most similar users
    based on their interaction patterns (collaborative filtering).

    Args:
        user_id: The ID of the user to get recommendations for.
        limit: Maximum recommendations to return.

    Returns:
        List of dicts: [{id, name, role, branch, skills, score, profile_pic, reason}, ...]
        Empty list if user has no interactions (cold start).
    """
    global _model_cache

    # Ensure model is trained
    if _model_cache['knn_model'] is None:
        success = train_knn_model()
        if not success:
            return []

    uid_to_idx = _model_cache['user_id_to_idx']
    idx_to_uid = _model_cache['idx_to_user_id']
    knn = _model_cache['knn_model']
    matrix = _model_cache['interaction_matrix']

    if user_id not in uid_to_idx:
        return []  # user not in matrix → cold start

    user_idx = uid_to_idx[user_id]
    user_vector = matrix[user_idx]

    # Cold start check: if user has no interactions at all
    if np.count_nonzero(user_vector) < MIN_INTERACTIONS:
        return []  # fallback to rule-based in hybrid_recommendation

    try:
        # Query KNN for nearest neighbors
        distances, indices = knn.kneighbors(
            user_vector.reshape(1, -1),
            n_neighbors=min(limit + 5, knn.n_neighbors)  # fetch extras to filter
        )

        # ----- Build exclusion set (self + already connected + pending) -----
        conn = get_db_connection()
        c = conn.cursor()

        excluded_ids = {user_id}

        connections = c.execute(
            'SELECT user_id_1, user_id_2 FROM connections WHERE user_id_1 = ? OR user_id_2 = ?',
            (user_id, user_id)
        ).fetchall()
        for row in connections:
            excluded_ids.add(row['user_id_1'] if row['user_id_1'] != user_id else row['user_id_2'])

        pending = c.execute(
            "SELECT sender_id, receiver_id FROM connection_requests "
            "WHERE (sender_id = ? OR receiver_id = ?) AND status = 'pending'",
            (user_id, user_id)
        ).fetchall()
        for row in pending:
            excluded_ids.add(row['sender_id'] if row['sender_id'] != user_id else row['receiver_id'])

        # Get current user's role for cross-role matching
        current_user_row = c.execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()
        if not current_user_row:
            conn.close()
            return []
        target_role = 'alumni' if current_user_row['role'] == 'student' else 'student'

        # ----- Build recommendations from KNN neighbors -----
        recommendations = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            neighbor_uid = idx_to_uid.get(int(idx))
            if neighbor_uid is None or neighbor_uid in excluded_ids:
                continue

            # Fetch neighbor profile
            neighbor = c.execute(
                'SELECT id, name, role, branch, skills, profile_pic FROM users WHERE id = ?',
                (neighbor_uid,)
            ).fetchone()
            if not neighbor or neighbor['role'] != target_role:
                continue

            # Cosine distance → similarity score (0–100 scale)
            similarity = max(0, round((1 - dist) * 100, 2))

            recommendations.append({
                'id': neighbor['id'],
                'name': neighbor['name'],
                'role': neighbor['role'],
                'branch': neighbor['branch'],
                'skills': neighbor['skills'],
                'score': similarity,
                'reason': 'ML: similar interactions',
                'profile_pic': neighbor['profile_pic'] or (
                    f"https://ui-avatars.com/api/?name={neighbor['name']}&background=random"
                )
            })

            if len(recommendations) >= limit:
                break

        conn.close()
        return recommendations

    except Exception as e:
        logger.error(f"[ML] get_ml_recommendations error: {e}")
        return []


# =====================================================================
# STEP 4:  Hybrid recommendation (ML + Rule-based with cold-start)
# =====================================================================
def hybrid_recommendation(user_id, limit=5):
    """
    Combines ML collaborative filtering with rule-based recommendations.

    Strategy:
      1. Try ML recommendations first.
      2. If ML returns fewer than `limit` (cold start or sparse data),
         fill remaining slots with rule-based recommendations.
      3. Deduplicate by user ID, preferring ML scores.
      4. Sort by score descending, return top `limit`.

    Args:
        user_id: The ID of the user.
        limit: Max recommendations to return.

    Returns:
        List of recommendation dicts with score and reason.

    FUTURE SCOPE:
      - Weighted ensemble: alpha * ML_score + (1 - alpha) * rule_score
      - Deep learning model (Graph Neural Networks)
      - Real-time update: retrain on new interaction events
      - Contextual bandits for exploration vs exploitation
    """
    from models.recommendation import get_rule_based_recommendations

    # --- Attempt ML recommendations ---
    ml_recs = get_ml_recommendations(user_id, limit=limit)

    seen_ids = set()
    final = []

    # Add ML results first (higher priority)
    for rec in ml_recs:
        if rec['id'] not in seen_ids:
            rec['source'] = 'ml'
            final.append(rec)
            seen_ids.add(rec['id'])

    # --- Fill remaining with rule-based (cold-start fallback) ---
    if len(final) < limit:
        rule_recs = get_rule_based_recommendations(user_id, limit=limit * 2)
        for rec in rule_recs:
            if rec['id'] not in seen_ids:
                rec['source'] = 'rule'
                final.append(rec)
                seen_ids.add(rec['id'])
            if len(final) >= limit:
                break

    # Sort by score descending
    final.sort(key=lambda x: x['score'], reverse=True)

    logger.info(f"[Hybrid] user_id={user_id} → "
                f"{sum(1 for r in final if r.get('source')=='ml')} ML + "
                f"{sum(1 for r in final if r.get('source')=='rule')} rule-based")

    return final[:limit]


# =====================================================================
# STEP 5:  Log user interactions (for future real-time tracking)
# =====================================================================
def log_interaction(user_id, target_user_id, interaction_type):
    """
    Log a user interaction into the user_interactions table.
    This data feeds into the ML model on next retrain.

    interaction_type: 'profile_view', 'job_click', 'mentorship_request',
                      'message', 'connection_request'
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            'INSERT INTO user_interactions (user_id, target_user_id, interaction_type) '
            'VALUES (?, ?, ?)',
            (user_id, target_user_id, interaction_type)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.debug(f"Could not log interaction: {e}")


# =====================================================================
# Model initialization helper (called from app startup)
# =====================================================================
def init_recommendation_engine(app=None):
    """
    Initialize the recommendation engine at app startup.
    Trains the KNN model in a background thread to avoid blocking.
    
    Args:
        app: Flask app instance (required for DB access in background thread)
    """
    def _train_bg():
        try:
            if app is not None:
                with app.app_context():
                    train_knn_model(force=True)
            else:
                train_knn_model(force=True)
        except Exception as e:
            logger.error(f"[ML] Background training failed: {e}")

    t = threading.Thread(target=_train_bg, daemon=True)
    t.start()
    logger.info("[ML] Recommendation engine initialization started (background)")
