from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q


@login_required
def notifications_page(request):
    """
    Full page view for all notifications with filters and pagination.
    """
    from .models import Notification
    
    # Get filter parameters
    filter_type = request.GET.get('type', 'all')  # all, unread, read
    notification_type = request.GET.get('notif_type', '')  # BUDGET, GOAL, etc
    
    # Base queryset
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Apply filters
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'read':
        notifications = notifications.filter(is_read=True)
    
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    # Pagination
    paginator = Paginator(notifications, 20)  # 20 per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Count statistics
    total_count = Notification.objects.filter(user=request.user).count()
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    read_count = Notification.objects.filter(user=request.user, is_read=True).count()
    
    # Get all notification types for filter
    notification_types = Notification.NotificationType.choices
    
    context = {
        'page_obj': page_obj,
        'filter_type': filter_type,
        'notification_type': notification_type,
        'notification_types': notification_types,
        'total_count': total_count,
        'unread_count': unread_count,
        'read_count': read_count,
    }
    
    return render(request, 'notifications/notifications_page.html', context)


@login_required
def notifications_list(request):
    """
    API endpoint to get user notifications.
    Returns JSON with unread count and notification list.
    """
    try:
        from .models import Notification
        
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:20]
        
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        notifications_data = []
        for notif in notifications:
            notifications_data.append({
                'id': notif.id,
                'type': notif.notification_type,
                'icon': notif.get_icon(),
                'color': notif.get_color_class(),
                'title': notif.title,
                'message': notif.message,
                'link': notif.link or '#',
                'is_read': notif.is_read,
                'created_at': notif.created_at.strftime('%d/%m/%Y %H:%M'),
                'time_ago': _get_time_ago(notif.created_at),
            })
        
        return JsonResponse({
            'unread_count': unread_count,
            'notifications': notifications_data
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'unread_count': 0,
            'notifications': []
        }, status=500)


@login_required
@require_POST
def mark_as_read(request, notification_id):
    """Mark a notification as read."""
    try:
        from .models import Notification
        
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user=request.user
        )
        
        notification.mark_as_read()
        
        # If AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        # Otherwise redirect to link
        return redirect(notification.link or 'notifications:notifications_page')
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def mark_all_as_read(request):
    """Mark all notifications as read."""
    try:
        from django.utils import timezone
        from .models import Notification
        
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        # Get the referer to redirect back
        referer = request.META.get('HTTP_REFERER', '/notifications/')
        return redirect(referer)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def delete_notification(request, notification_id):
    """Delete a notification."""
    try:
        from .models import Notification
        
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user=request.user
        )
        
        notification.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        # Get the referer to redirect back
        referer = request.META.get('HTTP_REFERER', '/notifications/')
        return redirect(referer)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def delete_all_read(request):
    """Delete all read notifications."""
    try:
        from .models import Notification
        
        count = Notification.objects.filter(
            user=request.user,
            is_read=True
        ).delete()[0]
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'count': count})
        
        from django.contrib import messages
        messages.success(request, f'✅ {count} notificação(ões) deletada(s)!')
        
        return redirect('notifications:notifications_page')
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def _get_time_ago(created_at):
    """Get human-readable time difference."""
    from django.utils import timezone
    
    now = timezone.now()
    diff = now - created_at
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'Agora mesmo'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'Há {minutes} minuto{"s" if minutes > 1 else ""}'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'Há {hours} hora{"s" if hours > 1 else ""}'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'Há {days} dia{"s" if days > 1 else ""}'
    else:
        return created_at.strftime('%d/%m/%Y')