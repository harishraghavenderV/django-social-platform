from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

class UserForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'cover_photo', 'location', 'website', 'interest_tags']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_interest_tags(self):
        tags = self.cleaned_data.get('interest_tags', '')
        if tags:
            tag_list = [t.strip() for t in tags.split(',') if t.strip()]
            if len(tag_list) > 5:
                raise forms.ValidationError("You can add up to 5 interest tags only.")
        return tags