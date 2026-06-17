from django import forms
from .models import Group


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'cover_image', 'is_private']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
