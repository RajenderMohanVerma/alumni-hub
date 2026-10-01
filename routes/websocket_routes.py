"""
WebSocket Handlers for Alumni Hub Messaging System
Real-time communication for public messages, private messages, typing indicators, and system events
"""

from flask import request
from flask_socketio import emit, join_room, leave_room, disconnect, rooms
from flask_login import current_user
from datetime import datetime
import json

from database.messaging_db import (
    send_private_message, mark_message_as_read, delete_private_message,
    get_conversation_messages, hide_all_public_messages, unhide_all_public_messages,
    send_public_message, is_messaging_locked, get_messaging_lock_status,
    mark_conversation_as_read, is_user_suspended
)

# Global dict to track online users
online_users = {}


def setup_websocket_handlers(socketio):
    """Setup all WebSocket event handlers"""

    @socketio.on('connect')
    def handle_connect():
        """Handle user connection"""
        if not current_user.is_authenticated:
            return False

        user_id = current_user.id
        online_users[user_id] = {
            'id': user_id,
            'name': current_user.name,
            'role': current_user.role,
            'session_id': request.sid,
            'connected_at': datetime.utcnow().isoformat()
        }

        # Join user to their personal room for private messages
        join_room(f'user_{user_id}')
        join_room('public_chat')

        # Admins automatically join the admin monitor room for real-time connection updates
        if current_user.role == 'admin':
            join_room('admin_monitor')

        # Broadcast user online status
        emit('user_online', {
            'user_id': user_id,
            'name': current_user.name,
            'role': current_user.role,
            'timestamp': datetime.utcnow().isoformat()
        }, room='public_chat')

        print(f"User {current_user.name} (ID: {user_id}) connected")

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle user disconnection"""
        if not current_user.is_authenticated:
            return

        user_id = current_user.id

        if user_id in online_users:
            del online_users[user_id]

        # Broadcast user offline status
        emit('user_offline', {
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room='public_chat', skip_sid=request.sid)

        print(f"User {current_user.name} (ID: {user_id}) disconnected")

    # ==================== PUBLIC MESSAGING ====================

    @socketio.on('send_public_message')
    def handle_send_public_message(data):
        """Handle sending a public message"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Not authenticated'})
            return

        if is_messaging_locked():
            emit('error', {'message': 'Public messaging is locked by admin'})
            return

        if is_user_suspended(current_user.id):
            emit('error', {'message': 'Your messaging privileges have been suspended'})
            return

        content = data.get('content', '').strip()

        if not content:
            emit('error', {'message': 'Message content cannot be empty'})
            return

        if len(content) > 5000:
            emit('error', {'message': 'Message exceeds maximum length'})
            return

        # Save to database
        message_id = send_public_message(current_user.id, content)

        if message_id:
            # Broadcast to all users in public chat
            message_data = {
                'id': message_id,
                'sender_id': current_user.id,
                'sender_name': current_user.name,
                'sender_role': current_user.role,
                'sender_pic': current_user.profile_pic,
                'content': content,
                'created_at': datetime.utcnow().isoformat(),
                'is_hidden': False
            }

            emit('receive_public_message', message_data, room='public_chat')
            emit('message_sent', {'message_id': message_id, 'status': 'success'})
        else:
            emit('error', {'message': 'Failed to send message'})

    @socketio.on('delete_public_message')
    def handle_delete_public_message(data):
        """Handle deleting a public message (admin only)"""
        if not current_user.is_authenticated or current_user.role != 'admin':
            emit('error', {'message': 'Unauthorized'})
            return

        message_id = data.get('message_id')

        if not message_id:
            emit('error', {'message': 'message_id required'})
            return

        from database.messaging_db import delete_public_message
        success = delete_public_message(message_id, current_user.id)

        if success:
            emit('message_deleted_public', {
                'message_id': message_id,
                'deleted_by': current_user.id,
                'timestamp': datetime.utcnow().isoformat()
            }, room='public_chat')

            emit('message_deleted', {'message_id': message_id, 'status': 'success'})
        else:
            emit('error', {'message': 'Message not found'})

    @socketio.on('lock_messaging')
    def handle_lock_messaging(data):
        """Lock public messaging (admin only)"""
        if not current_user.is_authenticated or current_user.role != 'admin':
            emit('error', {'message': 'Unauthorized'})
            return

        reason = data.get('reason', '')

        from database.messaging_db import lock_messaging
        hide_all_public_messages()
        success = lock_messaging(current_user.id, reason)

        if success:
            emit('system_locked', {
                'reason': reason,
                'locked_by': current_user.name,
                'locked_at': datetime.utcnow().isoformat()
            }, room='public_chat')

            emit('lock_success', {'status': 'locked'})
        else:
            emit('error', {'message': 'Failed to lock messaging'})

    @socketio.on('unlock_messaging')
    def handle_unlock_messaging():
        """Unlock public messaging (admin only)"""
        if not current_user.is_authenticated or current_user.role != 'admin':
            emit('error', {'message': 'Unauthorized'})
            return

        from database.messaging_db import unlock_messaging
        unhide_all_public_messages()
        success = unlock_messaging()

        if success:
            emit('system_unlocked', {
                'unlocked_by': current_user.name,
                'unlocked_at': datetime.utcnow().isoformat()
            }, room='public_chat')

            emit('unlock_success', {'status': 'unlocked'})
        else:
            emit('error', {'message': 'Failed to unlock messaging'})

    # ==================== PRIVATE MESSAGING ====================

    @socketio.on('send_private_message')
    def handle_send_private_message(data):
        """Handle sending a private message"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Not authenticated'})
            return

        if is_user_suspended(current_user.id):
            emit('error', {'message': 'Your messaging privileges have been suspended'})
            return

        receiver_id = data.get('receiver_id')
        content = data.get('content', '').strip()

        if not receiver_id:
            emit('error', {'message': 'receiver_id required'})
            return

        if not content:
            emit('error', {'message': 'Message content cannot be empty'})
            return

        if len(content) > 5000:
            emit('error', {'message': 'Message exceeds maximum length'})
            return

        if current_user.id == receiver_id:
            emit('error', {'message': 'Cannot send message to yourself'})
            return

        # Save to database
        message_id = send_private_message(current_user.id, receiver_id, content)

        if message_id:
            message_data = {
                'id': message_id,
                'sender_id': current_user.id,
                'sender_name': current_user.name,
                'receiver_id': receiver_id,
                'content': content,
                'is_read': False,
                'created_at': datetime.utcnow().isoformat()
            }

            # Send to receiver if online
            emit('receive_private_message', message_data, room=f'user_{receiver_id}')

            # Confirm to sender
            emit('message_sent', {
                'message_id': message_id,
                'status': 'success',
                'receiver_id': receiver_id
            })
        else:
            emit('error', {'message': 'Failed to send message'})

    @socketio.on('mark_message_read')
    def handle_mark_read(data):
        """Mark a private message as read"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Not authenticated'})
            return

        message_id = data.get('message_id')
        sender_id = data.get('sender_id')

        if not message_id or not sender_id:
            emit('error', {'message': 'message_id and sender_id required'})
            return

        success = mark_message_as_read(message_id, current_user.id)

        if success:
            emit('message_read', {
                'message_id': message_id,
                'read_at': datetime.utcnow().isoformat()
            }, room=f'user_{sender_id}')

            emit('read_success', {'message_id': message_id})
        else:
            emit('error', {'message': 'Failed to mark as read'})

    @socketio.on('mark_conversation_read')
    def handle_mark_conversation_read(data):
        """Mark all messages in a conversation as read"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Not authenticated'})
            return

        other_user_id = data.get('other_user_id')

        if not other_user_id:
            emit('error', {'message': 'other_user_id required'})
            return

        count = mark_conversation_as_read(current_user.id, other_user_id, current_user.id)

        if count > 0:
            emit('conversation_read', {
                'other_user_id': other_user_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f'user_{other_user_id}')

            emit('read_success', {'status': 'conversation_marked'})

    @socketio.on('delete_private_message')
    def handle_delete_private_message(data):
        """Delete a private message"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Not authenticated'})
            return

        message_id = data.get('message_id')
        other_user_id = data.get('other_user_id')

        if not message_id or not other_user_id:
            emit('error', {'message': 'message_id and other_user_id required'})
            return

        success = delete_private_message(message_id, current_user.id)

        if success:
            emit('message_deleted_private', {
                'message_id': message_id,
                'deleted_by': current_user.id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f'user_{other_user_id}')

            emit('delete_success', {'message_id': message_id})
        else:
            emit('error', {'message': 'Failed to delete message'})

    # ==================== TYPING INDICATORS ====================

    @socketio.on('typing_public')
    def handle_typing_public(data):
        """Handle typing indicator in public chat"""
        if not current_user.is_authenticated:
            return

        emit('user_typing_public', {
            'user_id': current_user.id,
            'user_name': current_user.name
        }, room='public_chat', skip_sid=request.sid)

    @socketio.on('stop_typing_public')
    def handle_stop_typing_public():
        """Handle stop typing in public chat"""
        if not current_user.is_authenticated:
            return

        emit('user_stopped_typing_public', {
            'user_id': current_user.id
        }, room='public_chat', skip_sid=request.sid)

    @socketio.on('typing_private')
    def handle_typing_private(data):
        """Handle typing indicator in private chat"""
        if not current_user.is_authenticated:
            return

        receiver_id = data.get('receiver_id')

        if not receiver_id:
            return

        emit('user_typing_private', {
            'user_id': current_user.id,
            'user_name': current_user.name,
            'receiver_id': receiver_id
        }, room=f'user_{receiver_id}')

    @socketio.on('stop_typing_private')
    def handle_stop_typing_private(data):
        """Handle stop typing in private chat"""
        if not current_user.is_authenticated:
            return

        receiver_id = data.get('receiver_id')

        if not receiver_id:
            return

        emit('user_stopped_typing_private', {
            'user_id': current_user.id,
            'receiver_id': receiver_id
        }, room=f'user_{receiver_id}')

    # ==================== UTILITY ENDPOINTS ====================

    @socketio.on('get_online_users')
    def handle_get_online_users():
        """Get list of currently online users"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Not authenticated'})
            return

        users_list = list(online_users.values())

        emit('online_users', {
            'users': users_list,
            'count': len(users_list)
        })

    @socketio.on('refresh_lock_status')
    def handle_refresh_lock_status():
        """Get current messaging lock status"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Not authenticated'})
            return

        status = get_messaging_lock_status()

        if status:
            emit('lock_status_update', {
                'is_locked': status['is_locked'],
                'reason': status['reason'],
                'locked_at': status['locked_at']
            })
        else:
            emit('error', {'message': 'Unable to fetch lock status'})

    @socketio.on('get_conversation_history')
    def handle_get_conversation_history(data):
        """Get conversation history with a user"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Not authenticated'})
            return

        other_user_id = data.get('other_user_id')
        limit = data.get('limit', 50)

        if not other_user_id:
            emit('error', {'message': 'other_user_id required'})
            return

        messages = get_conversation_messages(current_user.id, other_user_id, limit=limit, offset=0)

        emit('conversation_history', {
            'messages': messages,
            'other_user_id': other_user_id
        })

    # Add from flask import request at the top
    @socketio.on('error')
    def handle_error(error):
        """Handle errors"""
        print(f"Socket error: {error}")
        return False
