from django import forms
from NewsPortal.models import Author


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['photo', 'description']

    username = forms.CharField(
        max_length=20,
        required=True,
        label='Никнейм'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username

    def save(self, commit=True):
        author = super().save(commit=False)
        if commit:
            # Обновляем username пользователя
            author.user.username = self.cleaned_data['username']
            author.user.save()
            author.save()
        return author