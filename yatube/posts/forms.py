from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_subject(self):
        text = self.cleaned_data['text']
        if text == '':
            raise forms.ValidationError('Поле не заполнено')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    def clean_subject(self):
        text = self.cleaned_data['text']
        if text == '':
            raise forms.ValidationError('Поле не заполнено')
