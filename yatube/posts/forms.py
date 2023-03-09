from django.forms import ModelForm

from .models import Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group',)
        labels = {
            'text': ('Текст'),
            'group': ('Группа'),
        }
        help_texts = {
            'text': 'Здесь можно написать свой великолепный пост',
            'group': 'Если нет подходящей группы, оставьте поле пустым'
        }
