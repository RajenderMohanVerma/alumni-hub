"""
models/recommendation.py
========================
PHASE 1 — Rule-Based Recommendation Engine (Improved)

Scoring Rules:
  - Same Department/Branch : +5 pts
  - Skill Match            : +5 pts per matching skill
  - Same Domain            : +3 pts
  - Passing Year Proximity : +4 pts (within 2 years), +2 pts (within 4 years)
  - Same City              : +2 pts
  - Mutual Connections     : +2 pts per mutual connection

FUTURE SCOPE:
  - Hybrid system combining rule-based + ML collaborative filtering
  - Deep learning embeddings (Sentence Transformers / GNNs)
  - Real-time model updates via streaming interaction data
"""

from db_utils import get_db_connection
import logging

logger = logging.getLogger(__name__)


def get_rule_based_recommendations(user_id, limit=5):
    """
    Improved Rule-Based Recommendation using profile similarity.

    Factors:
      1. skills        — +5 per matching skill
      2. department     — +5 if same branch
      3. domain         — +3 if same current_domain
      4. passing_year   — +4 (within 2 yrs), +2 (within 4 yrs)
      5. city           — +2 if same city
      6. mutual conns   — +2 per mutual connection

    Args:
        user_id: ID of the current user
        limit: Max number of recommendations to return (default 5)

    Returns:
        List of dicts with id, name, role, branch, skills, score, profile_pic, reason
    """
    conn = get_db_connection()
    c = conn.cursor()

    try:
        # Fetch current user
        user_row = c.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user_row:
            return []

        user = dict(user_row)
        if user['role'] not in ('student', 'alumni'):
            return []

        # Target role: students see alumni, alumni see students
        target_role = 'alumni' if user['role'] == 'student' else 'student'

        # ----- Build exclusion set (self + connected + pending) -----
        excluded_ids = {user_id}

        connections = c.execute(
            'SELECT user_id_1, user_id_2 FROM connections WHERE user_id_1 = ? OR user_id_2 = ?',
            (user_id, user_id)
        ).fetchall()
        for row in connections:
            excluded_ids.add(row['user_id_1'] if row['user_id_1'] != user_id else row['user_id_2'])

        pending = c.execute(
            'SELECT sender_id, receiver_id FROM connection_requests '
            'WHERE (sender_id = ? OR receiver_id = ?) AND status = "pending"',
            (user_id, user_id)
        ).fetchall()
        for row in pending:
            excluded_ids.add(row['sender_id'] if row['sender_id'] != user_id else row['receiver_id'])

        # ----- Current user's direct connections (for mutual calc) -----
        user_conn_ids = set()
        for row in connections:
            user_conn_ids.add(row['user_id_1'] if row['user_id_1'] != user_id else row['user_id_2'])

        # ----- Fetch candidates -----
        placeholders = ','.join(['?'] * len(excluded_ids))
        candidates = c.execute(
            f'SELECT * FROM users WHERE role = ? AND id NOT IN ({placeholders}) LIMIT 50',
            [target_role] + list(excluded_ids)
        ).fetchall()

        if not candidates:
            return []

        # ----- Pre-fetch candidate connections for mutual calculation -----
        candidate_ids = [cand['id'] for cand in candidates]
        ph = ','.join(['?'] * len(candidate_ids))
        all_cand_conns = c.execute(
            f'SELECT user_id_1, user_id_2 FROM connections '
            f'WHERE user_id_1 IN ({ph}) OR user_id_2 IN ({ph})',
            candidate_ids + candidate_ids
        ).fetchall()

        cand_conn_map = {cid: set() for cid in candidate_ids}
        for row in all_cand_conns:
            u1, u2 = row['user_id_1'], row['user_id_2']
            if u1 in cand_conn_map:
                cand_conn_map[u1].add(u2)
            if u2 in cand_conn_map:
                cand_conn_map[u2].add(u1)

        # ----- Parse current user's skills -----
        user_skills = set(
            s.strip().lower() for s in (user.get('skills') or '').split(',') if s.strip()
        )
        user_pass_year = user.get('passing_year')

        # ----- Score each candidate -----
        recommendations = []
        for cand in candidates:
            score = 0
            reasons = []

            # Rule 1: Same branch / department (+5)
            if (cand['branch'] and user.get('branch') and
                    cand['branch'].lower() == user['branch'].lower()):
                score += 5
                reasons.append('Same branch')

            # Rule 2: Skill match (+5 per matching skill)
            cand_skills = set(
                s.strip().lower() for s in (cand['skills'] or '').split(',') if s.strip()
            )
            common_skills = user_skills & cand_skills
            if common_skills:
                score += len(common_skills) * 5
                reasons.append(f'{len(common_skills)} skill match')

            # Rule 3: Same domain (+3)
            if (cand['current_domain'] and user.get('current_domain') and
                    cand['current_domain'].lower() == user['current_domain'].lower()):
                score += 3
                reasons.append('Same domain')

            # Rule 4: Passing year proximity (+4 within 2 yrs, +2 within 4 yrs)
            cand_pass_year = cand['passing_year']
            if user_pass_year and cand_pass_year:
                year_diff = abs(int(user_pass_year) - int(cand_pass_year))
                if year_diff <= 2:
                    score += 4
                    reasons.append('Close batch')
                elif year_diff <= 4:
                    score += 2
                    reasons.append('Similar batch')

            # Rule 5: Same city (+2)
            if (cand['city'] and user.get('city') and
                    cand['city'].lower() == user['city'].lower()):
                score += 2
                reasons.append('Same city')

            # Rule 6: Mutual connections (+2 per mutual)
            if cand['id'] in cand_conn_map:
                mutuals = cand_conn_map[cand['id']].intersection(user_conn_ids)
                if mutuals:
                    score += len(mutuals) * 2
                    reasons.append(f'{len(mutuals)} mutual')

            if score > 0:
                recommendations.append({
                    'id': cand['id'],
                    'name': cand['name'],
                    'role': cand['role'],
                    'branch': cand['branch'],
                    'skills': cand['skills'],
                    'score': round(score, 2),
                    'reason': ', '.join(reasons),
                    'profile_pic': cand['profile_pic'] or (
                        f"https://ui-avatars.com/api/?name={cand['name']}&background=random"
                    )
                })

        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]

    except Exception as e:
        logger.error(f"Rule-based recommendation error: {e}")
        return []
    finally:
        conn.close()


# ----------- Backward-compatible wrapper (used by dashboard routes) -----------
def get_recommended_users(user):
    """
    Backward-compatible wrapper called from dashboard routes.
    Delegates to hybrid_recommendation when ML engine is available,
    otherwise falls back to rule-based only.
    """
    if not user or not hasattr(user, 'id') or not user.id:
        return []
    if hasattr(user, 'role') and user.role not in ('student', 'alumni'):
        return []

    try:
        # Try hybrid (ML + rule-based) first
        from services.recommendation_engine import hybrid_recommendation
        return hybrid_recommendation(user.id)
    except Exception as e:
        logger.warning(f"ML engine unavailable, falling back to rule-based: {e}")
        return get_rule_based_recommendations(user.id)


def get_recommended_jobs(user):
    """
    Job Recommendation Engine
    - Matches user skills against job requirements.
    - Limits to Top 5 matches.
    """
    if not user or not hasattr(user, 'role') or user.role != 'student' or not user.id:
        return []

    conn = get_db_connection()
    c = conn.cursor()

    try:
        # Fetch active jobs
        jobs = c.execute('''
            SELECT j.*, u.name as posted_by_name
            FROM jobs j
            JOIN users u ON j.posted_by = u.id
            ORDER BY j.created_at DESC
        ''').fetchall()

        user_skills = set(
            s.strip().lower() for s in (user.skills or '').split(',') if s.strip()
        )
        recommended = []

        for job in jobs:
            job_skills = set(
                s.strip().lower() for s in (job['required_skills'] or '').split(',') if s.strip()
            )
            match_count = len(user_skills & job_skills)

            if match_count > 0:
                job_dict = dict(job)
                job_dict['match_score'] = match_count
                recommended.append(job_dict)

        recommended.sort(key=lambda x: x['match_score'], reverse=True)
        return recommended[:5]

    except Exception as e:
        logger.error(f"Job recommendation error: {e}")
        return []
    finally:
        conn.close()
