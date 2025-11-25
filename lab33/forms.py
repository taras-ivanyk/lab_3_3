from django import forms
from activities.models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['activity', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'cols': 40, 'rows': 3}),
        }