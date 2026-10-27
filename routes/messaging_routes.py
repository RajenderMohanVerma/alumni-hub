"""
Messaging Routes for Alumni Hub
Handles all API endpoints for public messages, private messages, search, and admin controls
"""

from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import login_required, current_user
from datetime import datetime
import json

from database.messaging_db import (
    get_db_connection,
    # Lock functions
    get_messaging_lock_status, lock_messaging, unlock_messaging, is_messaging_locked,
    # Public message functions
    send_public_message, get_public_messages, delete_public_message,
    hide_all_public_messages, unhide_all_public_messages, get_public_message_count,
    # Private message functions
    send_private_message, get_conversation_messages, get_user_conversations,
    mark_message_as_read, mark_conversation_as_read, delete_private_message,
    get_unread_message_count,
    # Search and management
    search_messages, create_conversation, get_conversation_id,
    get_messaging_statistics,
    # Suspension functions
    is_user_suspended, suspend_user, unsuspend_user, get_suspended_users,
    # Community group functions
    get_community_member_status, request_community_membership,
    approve_community_member, reject_community_member, remove_community_member,
    get_pending_community_requests, get_approved_community_members,
    send_community_message, get_community_messages, delete_community_message
)

messaging_bp = Blueprint('messaging', __name__)


# ==================== HELPER FUNCTIONS ====================

def require_admin():
    """Check if user is admin"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        return False
    return True


def get_user_dict(user):
    """Convert user object to dictionary"""
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'profile_pic': user.profile_pic,
        'role': user.role
    }


# ==================== PUBLIC MESSAGING ENDPOINTS ====================

@messaging_bp.route('/messages/public', methods=['POST'])
@login_required
def send_public_msg():
    """Send a public message"""
    if is_messaging_locked():
        return jsonify({
            'success': False,
            'message': 'Public messaging is currently locked by admin'
        }), 403

    if is_user_suspended(current_user.id):
        return jsonify({
            'success': False,
            'message': 'Your messaging privileges have been suspended'
        }), 403

    data = request.get_json()
    content = data.get('content', '').strip()

    if not content:
        return jsonify({
            'success': False,
            'message': 'Message content cannot be empty'
        }), 400

    if len(content) > 5000:
        return jsonify({
            'success': False,
            'message': 'Message content exceeds maximum length (5000 characters)'
        }), 400

    message_id = send_public_message(current_user.id, content)

    if message_id:
        return jsonify({
            'success': True,
            'message_id': message_id,
            'created_at': datetime.utcnow().isoformat()
        }), 201
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to send message'
        }), 500


@messaging_bp.route('/messages/public', methods=['GET'])
@login_required
def get_public_msgs():
    """Get public messages with pagination"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    limit = min(limit, 100)  # Max 100 messages per request

    # Admin can see hidden messages
    include_hidden = current_user.role == 'admin' and request.args.get('include_hidden', False, type=bool)

    messages = get_public_messages(limit=limit, offset=offset, include_hidden=include_hidden)

    return jsonify({
        'success': True,
        'messages': messages,
        'total': get_public_message_count(),
        'limit': limit,
        'offset': offset
    }), 200


@messaging_bp.route('/messages/public/<int:message_id>', methods=['DELETE'])
@login_required
def delete_public_msg(message_id):
    """Delete a public message (admin only)"""
    if current_user.role != 'admin':
        return jsonify({
            'success': False,
            'message': 'Only admins can delete messages'
        }), 403

    success = delete_public_message(message_id, current_user.id)

    if success:
        return jsonify({
            'success': True,
            'message': 'Message deleted successfully'
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Message not found'
        }), 404


# ==================== PRIVATE MESSAGING ENDPOINTS ====================

@messaging_bp.route('/messages/private', methods=['POST'])
@login_required
def send_private_msg():
    """Send a private message"""
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content', '').strip()

    if is_messaging_locked() and current_user.role != 'admin':
        return jsonify({
            'success': False,
            'message': 'Direct 1-on-1 messaging is temporarily locked by administrator.'
        }), 403

    if is_user_suspended(current_user.id):
        return jsonify({
            'success': False,
            'message': 'Your messaging privileges have been suspended'
        }), 403

    if not receiver_id:
        return jsonify({
            'success': False,
            'message': 'receiver_id is required'
        }), 400

    if not content:
        return jsonify({
            'success': False,
            'message': 'Message content cannot be empty'
        }), 400

    if len(content) > 5000:
        return jsonify({
            'success': False,
            'message': 'Message content exceeds maximum length (5000 characters)'
        }), 400

    if current_user.id == receiver_id:
        return jsonify({
            'success': False,
            'message': 'Cannot send message to yourself'
        }), 400

    # For non-admin roles: verify recipient is in connections circle or is admin
    if current_user.role != 'admin':
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT role FROM users WHERE id = ?', (receiver_id,))
            target = cursor.fetchone()
            if not target:
                return jsonify({'success': False, 'message': 'Recipient not found'}), 404
            
            if target['role'] != 'admin':
                cursor.execute('''
                    SELECT 1 FROM connections
                    WHERE (user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?)
                ''', (current_user.id, receiver_id, receiver_id, current_user.id))
                if not cursor.fetchone():
                    return jsonify({
                        'success': False,
                        'message': 'You can only message users who are in your connections / network.'
                    }), 403

    # Check if receiver is online (net/socket active)
    from routes.websocket_routes import is_user_online
    receiver_online = is_user_online(receiver_id)
    now_iso = datetime.utcnow().isoformat() + 'Z'

    message_id = send_private_message(current_user.id, receiver_id, content, is_delivered=receiver_online)

    if message_id:
        msg_obj = {
            'id': message_id,
            'sender_id': current_user.id,
            'sender_name': current_user.name,
            'sender_role': current_user.role,
            'receiver_id': receiver_id,
            'content': content,
            'is_delivered': receiver_online,
            'is_read': False,
            'created_at': now_iso
        }
        try:
            from app import socketio
            if receiver_online:
                socketio.emit('receive_private_message', msg_obj, room=f'user_{receiver_id}')
                socketio.emit('messages_delivered', {
                    'receiver_id': receiver_id,
                    'timestamp': now_iso
                }, room=f'user_{current_user.id}')
        except Exception:
            pass

        return jsonify({
            'success': True,
            'message_id': message_id,
            'message': msg_obj,
            'created_at': now_iso
        }), 201
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to send message'
        }), 500


@messaging_bp.route('/messages/private/<int:conversation_id>', methods=['GET'])
@login_required
def get_private_msgs(conversation_id):
    """Get messages in a conversation"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    limit = min(limit, 100)

    # Parse user IDs from conversation ID (would need proper conversation ID handling in production)
    # For now, we'll need to update this based on actual implementation
    # This is a placeholder - should be updated to fetch from conversations table

    return jsonify({
        'success': True,
        'message': 'Conversation endpoint - needs proper implementation'
    }), 200


@messaging_bp.route('/messages/inbox', methods=['GET'])
@login_required
def get_inbox():
    """Get user's inbox with all conversations"""
    conversations = get_user_conversations(current_user.id)

    return jsonify({
        'success': True,
        'conversations': conversations,
        'unread_count': get_unread_message_count(current_user.id)
    }), 200


@messaging_bp.route('/messages/private/<int:message_id>/read', methods=['POST'])
@login_required
def mark_read(message_id):
    """Mark a private message as read"""
    success = mark_message_as_read(message_id, current_user.id)

    if success:
        return jsonify({
            'success': True,
            'message': 'Message marked as read'
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Message not found or already read'
        }), 404


@messaging_bp.route('/messages/private/<int:message_id>', methods=['DELETE'])
@login_required
def delete_private_msg(message_id):
    """Delete a private message"""
    success = delete_private_message(message_id, current_user.id)

    if success:
        return jsonify({
            'success': True,
            'message': 'Message deleted successfully'
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Message not found or unauthorized'
        }), 404


# ==================== CONVERSATION ENDPOINTS ====================

@messaging_bp.route('/messages/conversation/create', methods=['POST'])
@login_required
def create_conv():
    """Create a conversation with another user"""
    data = request.get_json()
    other_user_id = data.get('other_user_id')

    if not other_user_id:
        return jsonify({
            'success': False,
            'message': 'other_user_id is required'
        }), 400

    if current_user.id == other_user_id:
        return jsonify({
            'success': False,
            'message': 'Cannot create conversation with yourself'
        }), 400

    # For non-admin roles: verify other user is in connections circle or is admin
    if current_user.role != 'admin':
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT role FROM users WHERE id = ?', (other_user_id,))
            target = cursor.fetchone()
            if not target:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            if target['role'] != 'admin':
                cursor.execute('''
                    SELECT 1 FROM connections
                    WHERE (user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?)
                ''', (current_user.id, other_user_id, other_user_id, current_user.id))
                if not cursor.fetchone():
                    return jsonify({
                        'success': False,
                        'message': 'You can only start conversations with users in your connections/friends circle.'
                    }), 403

    conv_id = create_conversation(current_user.id, other_user_id)

    return jsonify({
        'success': True,
        'conversation_id': conv_id
    }), 201


@messaging_bp.route('/messages/conversation/<int:user_id>/messages', methods=['GET'])
@login_required
def get_conv_messages(user_id):
    """Get all messages with a specific user"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        limit = min(limit, 100)

        messages = get_conversation_messages(current_user.id, user_id, limit=limit, offset=offset)

        # Mark all as read
        try:
            marked_count = mark_conversation_as_read(current_user.id, user_id, current_user.id)
            if marked_count > 0:
                from app import socketio
                socketio.emit('conversation_read', {
                    'reader_id': current_user.id,
                    'other_user_id': user_id,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }, room=f'user_{user_id}')
        except Exception as sock_err:
            print(f"Error marking/emitting conversation_read: {sock_err}")

        # Fetch other user details
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, email, role, phone, profile_pic FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            other_user = dict(row) if row else None

        return jsonify({
            'success': True,
            'other_user': other_user,
            'messages': messages
        }), 200
    except Exception as e:
        print(f"Error in get_conv_messages: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@messaging_bp.route('/messages/users', methods=['GET'])
@login_required
def get_messaging_users():
    """Get all eligible users for starting or filtering conversations across all roles.
    Admins can see all approved users across the platform.
    Non-admins (Student, Alumni, Faculty) can ONLY see users in their connections circle + Admins.
    Both can filter by role and search by name or email.
    """
    role = request.args.get('role', 'all').lower()
    search = request.args.get('search', '').strip().lower()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if current_user.role == 'admin':
            # Admin can view and message anyone in the system
            query = '''
                SELECT id, name, email, role, phone, profile_pic
                FROM users
                WHERE id != ? AND is_approved = 1
            '''
            params = [current_user.id]

            if role != 'all' and role in ['student', 'alumni', 'faculty', 'admin']:
                query += ' AND role = ?'
                params.append(role)

            if search:
                query += ' AND (LOWER(name) LIKE ? OR LOWER(email) LIKE ? OR LOWER(role) LIKE ?)'
                term = f"%{search}%"
                params.extend([term, term, term])

            query += ' ORDER BY name ASC'
        else:
            # Non-admin: ONLY connected users (friends/network) + Admins
            query = '''
                SELECT DISTINCT u.id, u.name, u.email, u.role, u.phone, u.profile_pic
                FROM users u
                LEFT JOIN connections c ON (
                    (c.user_id_1 = ? AND c.user_id_2 = u.id) OR
                    (c.user_id_2 = ? AND c.user_id_1 = u.id)
                )
                WHERE u.id != ? AND u.is_approved = 1
                  AND (c.id IS NOT NULL OR u.role = 'admin')
            '''
            params = [current_user.id, current_user.id, current_user.id]

            if role != 'all' and role in ['student', 'alumni', 'faculty', 'admin']:
                query += ' AND u.role = ?'
                params.append(role)

            if search:
                query += ' AND (LOWER(u.name) LIKE ? OR LOWER(u.email) LIKE ? OR LOWER(u.role) LIKE ?)'
                term = f"%{search}%"
                params.extend([term, term, term])

            query += ' ORDER BY u.name ASC'

        cursor.execute(query, tuple(params))
        users = [dict(row) for row in cursor.fetchall()]

    return jsonify({
        'success': True,
        'users': users
    }), 200


# ==================== SEARCH ENDPOINTS ====================

@messaging_bp.route('/messages/search', methods=['GET'])
@login_required
def search_msgs():
    """Search messages by query"""
    query = request.args.get('q', '').strip()
    message_type = request.args.get('type', 'all')  # 'public', 'private', 'all'
    limit = request.args.get('limit', 20, type=int)

    if not query or len(query) < 2:
        return jsonify({
            'success': False,
            'message': 'Query must be at least 2 characters'
        }), 400

    limit = min(limit, 50)

    # For private search, pass user_id
    user_id = current_user.id if message_type in ['private', 'all'] else None
    results = search_messages(query, user_id=user_id, message_type=message_type, limit=limit)

    return jsonify({
        'success': True,
        'results': results,
        'count': len(results)
    }), 200


# ==================== ADMIN ENDPOINTS ====================

@messaging_bp.route('/admin/messaging/lock', methods=['POST'])
@login_required
def lock_msg_system():
    """Lock public messaging system (admin only)"""
    if current_user.role != 'admin':
        return jsonify({
            'success': False,
            'message': 'Only admins can lock messaging'
        }), 403

    data = request.get_json()
    reason = data.get('reason', '')

    # Hide all public messages
    hide_all_public_messages()

    # Update lock status
    success = lock_messaging(current_user.id, reason)

    if success:
        try:
            from app import socketio
            socketio.emit('system_locked', {
                'locked_by': current_user.name,
                'locked_at': datetime.utcnow().isoformat()
            })
        except Exception:
            pass
        return jsonify({
            'success': True,
            'message': 'Messaging system locked',
            'locked_at': datetime.utcnow().isoformat()
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to lock messaging system'
        }), 500


@messaging_bp.route('/admin/messaging/unlock', methods=['POST'])
@login_required
def unlock_msg_system():
    """Unlock public messaging system (admin only)"""
    if current_user.role != 'admin':
        return jsonify({
            'success': False,
            'message': 'Only admins can unlock messaging'
        }), 403

    # Show all public messages
    unhide_all_public_messages()

    # Update lock status
    success = unlock_messaging()

    if success:
        try:
            from app import socketio
            socketio.emit('system_unlocked', {
                'unlocked_by': current_user.name,
                'unlocked_at': datetime.utcnow().isoformat()
            })
        except Exception:
            pass
        return jsonify({
            'success': True,
            'message': 'Messaging system unlocked'
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to unlock messaging system'
        }), 500


@messaging_bp.route('/admin/messaging/status', methods=['GET'])
@login_required
def get_lock_status():
    """Get current messaging lock status"""
    status = get_messaging_lock_status()

    if status:
        return jsonify({
            'success': True,
            'is_locked': status['is_locked'],
            'locked_by': status['locked_by'],
            'locked_at': status['locked_at'],
            'reason': status['reason']
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Unable to fetch lock status'
        }), 500


@messaging_bp.route('/admin/messaging/statistics', methods=['GET'])
@login_required
def get_stats():
    """Get messaging system statistics (admin only)"""
    if current_user.role != 'admin':
        return jsonify({
            'success': False,
            'message': 'Only admins can view statistics'
        }), 403

    stats = get_messaging_statistics()

    return jsonify({
        'success': True,
        'statistics': stats
    }), 200


@messaging_bp.route('/admin/messaging/public-messages', methods=['GET'])
@login_required
def get_all_public_messages():
    """Get all public messages for moderation (admin only)"""
    if current_user.role != 'admin':
        return jsonify({
            'success': False,
            'message': 'Only admins can view all messages'
        }), 403

    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    include_hidden = request.args.get('include_hidden', True, type=bool)

    limit = min(limit, 200)

    messages = get_public_messages(limit=limit, offset=offset, include_hidden=include_hidden)

    return jsonify({
        'success': True,
        'messages': messages,
        'total': get_public_message_count()
    }), 200


@messaging_bp.route('/admin/messaging/suspend', methods=['POST'])
@login_required
def suspend_user_route():
    """Suspend a user from messaging (admin only)"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json()
    user_id = data.get('user_id')
    reason = data.get('reason', '')

    if not user_id:
        return jsonify({'success': False, 'message': 'user_id is required'}), 400

    success = suspend_user(user_id, current_user.id, reason)

    if success:
        return jsonify({'success': True, 'message': 'User suspended successfully'}), 200
    else:
        return jsonify({'success': False, 'message': 'Failed to suspend user or user not found'}), 404


@messaging_bp.route('/admin/messaging/unsuspend', methods=['POST'])
@login_required
def unsuspend_user_route():
    """Unsuspend a user (admin only)"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': 'user_id is required'}), 400

    success = unsuspend_user(user_id)

    if success:
        return jsonify({'success': True, 'message': 'User unsuspended successfully'}), 200
    else:
        return jsonify({'success': False, 'message': 'Failed to unsuspend user or user not found'}), 404


@messaging_bp.route('/admin/messaging/suspended-users', methods=['GET'])
@login_required
def list_suspended_users():
    """Get list of suspended users (admin only)"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    users = get_suspended_users()

    return jsonify({
        'success': True,
        'users': users
    }), 200


# ==================== COMMUNITY GROUP (WHATSAPP-STYLE) ENDPOINTS ====================

@messaging_bp.route('/community-group/status', methods=['GET'])
@login_required
def api_community_group_status():
    """Get current user's membership status and group telemetry"""
    is_admin = (current_user.role == 'admin')
    status = 'approved' if is_admin else get_community_member_status(current_user.id)
    is_locked = is_messaging_locked()
    members = get_approved_community_members()

    return jsonify({
        'success': True,
        'status': status,
        'is_locked': is_locked,
        'member_count': len(members),
        'user_id': current_user.id,
        'user_name': current_user.name,
        'user_role': current_user.role
    }), 200


@messaging_bp.route('/community-group/join-request', methods=['POST'])
@login_required
def api_community_group_request():
    """User requests admission to the institutional community group"""
    if current_user.role == 'admin':
        return jsonify({'success': True, 'message': 'Admins have automatic membership', 'status': 'approved'}), 200

    request_community_membership(current_user.id)
    return jsonify({
        'success': True,
        'message': 'Your request has been submitted to Administrators for approval.',
        'status': 'pending'
    }), 200


@messaging_bp.route('/community-group/messages', methods=['GET', 'POST'])
@login_required
def api_community_group_messages():
    """Fetch or post messages in the community group"""
    is_admin = (current_user.role == 'admin')
    membership_status = 'approved' if is_admin else get_community_member_status(current_user.id)

    if membership_status != 'approved':
        return jsonify({
            'success': False,
            'message': 'You must be an approved member to access Community Group messages.',
            'status': membership_status
        }), 403

    if request.method == 'POST':
        # Enforce lock!
        if is_messaging_locked() and not is_admin:
            return jsonify({
                'success': False,
                'message': 'Community group messaging is temporarily frozen by Administrator.'
            }), 403

        if is_user_suspended(current_user.id):
            return jsonify({
                'success': False,
                'message': 'Your messaging privileges have been suspended.'
            }), 403

        data = request.get_json(silent=True) or request.form
        content = (data.get('content') or '').strip()

        if not content:
            return jsonify({'success': False, 'message': 'Message content cannot be empty'}), 400

        if len(content) > 5000:
            return jsonify({'success': False, 'message': 'Message exceeds 5000 character limit'}), 400

        msg_id = send_community_message(current_user.id, content)
        if msg_id:
            now_iso = datetime.utcnow().isoformat() + 'Z'
            msg_obj = {
                'id': msg_id,
                'sender_id': current_user.id,
                'sender_name': current_user.name,
                'sender_role': current_user.role,
                'sender_pic': current_user.profile_pic,
                'content': content,
                'created_at': now_iso
            }

            # Broadcast through Socket.IO room if socketio is active
            try:
                from app import socketio
                socketio.emit('receive_community_message', msg_obj, room='community_group')
            except Exception:
                pass

            return jsonify({'success': True, 'message': msg_obj}), 201
        else:
            return jsonify({'success': False, 'message': 'Failed to record message'}), 500

    # GET request
    messages = get_community_messages(limit=80)
    return jsonify({
        'success': True,
        'messages': messages,
        'is_locked': is_messaging_locked()
    }), 200


@messaging_bp.route('/admin/community-group/requests', methods=['GET'])
@login_required
def api_admin_community_requests():
    """Admin retrieves list of pending requests to join community group"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    requests = get_pending_community_requests()
    return jsonify({'success': True, 'requests': requests}), 200


@messaging_bp.route('/admin/community-group/approve', methods=['POST'])
@login_required
def api_admin_approve_community_member():
    """Admin approves user admission to community group"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'user_id is required'}), 400

    approve_community_member(user_id, current_user.id)
    return jsonify({'success': True, 'message': 'User admitted to community group'}), 200


@messaging_bp.route('/admin/community-group/reject', methods=['POST'])
@login_required
def api_admin_reject_community_member():
    """Admin rejects admission request"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'user_id is required'}), 400

    reject_community_member(user_id, current_user.id)
    return jsonify({'success': True, 'message': 'Request rejected'}), 200


@messaging_bp.route('/admin/community-group/remove-member', methods=['POST'])
@login_required
def api_admin_remove_community_member():
    """Admin removes member from community group"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'user_id is required'}), 400

    remove_community_member(user_id)
    return jsonify({'success': True, 'message': 'Member removed from group'}), 200


@messaging_bp.route('/admin/community-group/members', methods=['GET'])
@login_required
def api_admin_community_members():
    """Admin gets list of all approved community members"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    members = get_approved_community_members()
    return jsonify({'success': True, 'members': members}), 200

