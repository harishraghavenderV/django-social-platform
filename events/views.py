from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import Event, EventRSVP
from .forms import EventForm

@login_required
def event_list(request):
    """List of upcoming or past events."""
    filter_type = request.GET.get('filter', 'upcoming')
    
    if filter_type == 'past':
        events = Event.objects.filter(start_datetime__lt=timezone.now()).order_by('-start_datetime')
    else:
        events = Event.objects.filter(start_datetime__gte=timezone.now()).order_by('start_datetime')
        
    user_rsvps = {}
    if request.user.is_authenticated:
        rsvps = EventRSVP.objects.filter(user=request.user, event__in=events)
        user_rsvps = {r.event_id: r.status for r in rsvps}
        
    return render(request, 'events/event_list.html', {
        'events': events,
        'user_rsvps': user_rsvps,
        'filter_type': filter_type,
    })

@login_required
def event_detail(request, pk):
    """Detailed information for an event including RSVPs."""
    event = get_object_or_404(Event, pk=pk)
    
    going_rsvps = event.rsvps.filter(status='going').select_related('user', 'user__userprofile')
    interested_rsvps = event.rsvps.filter(status='interested').select_related('user', 'user__userprofile')
    
    user_rsvp = event.rsvps.filter(user=request.user).first()
    user_rsvp_status = user_rsvp.status if user_rsvp else None
    
    return render(request, 'events/event_detail.html', {
        'event': event,
        'going_rsvps': going_rsvps,
        'interested_rsvps': interested_rsvps,
        'user_rsvp_status': user_rsvp_status,
    })

@login_required
def create_event(request):
    """Create a new event."""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.creator = request.user
            event.save()
            
            # Creator is auto RSVPed as going
            EventRSVP.objects.create(event=event, user=request.user, status='going')
            
            return redirect('events:event_detail', pk=event.pk)
    else:
        form = EventForm()
        
    return render(request, 'events/create_event.html', {'form': form})

@login_required
def event_rsvp(request, pk):
    """AJAX event RSVP view."""
    event = get_object_or_404(Event, pk=pk)
    status = request.POST.get('status')
    
    if status not in ['going', 'interested', 'not_going', 'remove']:
        return JsonResponse({'success': False, 'error': 'Invalid RSVP status'}, status=400)
        
    if status == 'remove':
        EventRSVP.objects.filter(event=event, user=request.user).delete()
        current_status = None
    else:
        rsvp, created = EventRSVP.objects.get_or_create(
            event=event,
            user=request.user,
            defaults={'status': status}
        )
        if not created:
            rsvp.status = status
            rsvp.save(update_fields=['status'])
        current_status = status
        
    return JsonResponse({
        'success': True,
        'current_status': current_status,
        'going_count': event.rsvp_count_by_status('going'),
        'interested_count': event.rsvp_count_by_status('interested'),
    })
