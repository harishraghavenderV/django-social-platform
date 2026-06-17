from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'cover_image', 'start_datetime', 'end_datetime', 'is_online', 'online_link']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Event Description'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Physical location or venue (optional)'}),
            'online_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://zoom.us/... (if online)'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_datetime')
        end = cleaned_data.get('end_datetime')
        is_online = cleaned_data.get('is_online')
        online_link = cleaned_data.get('online_link')

        if start and end and start > end:
            raise forms.ValidationError("End date/time must be after start date/time.")

        if is_online and not online_link:
            raise forms.ValidationError("Please provide an online link if this event is online.")

        return cleaned_data
