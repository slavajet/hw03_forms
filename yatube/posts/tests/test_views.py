from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()
NUMBER_OF_POSTS = 13


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='slava')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        for i in range(NUMBER_OF_POSTS):
            Post.objects.create(
                text='Тестовый пост',
                author=cls.user,
                group=cls.group,
                id=(1 + i),
            )
        cls.posts = Post.objects.all()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.posts[1].id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.posts[1].id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Шаблоны 'index', 'group_list' и 'posts:profile'
        сформированы с правильным контекстом."""
        templates_url_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user}),
        )
        for template in templates_url_names:
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                context_with_post = response.context['page_obj'][0]
                self.assertEqual(context_with_post.text, self.posts[0].text)
                self.assertEqual(context_with_post.id, self.posts[0].id)
                self.assertEqual(
                    context_with_post.author.username,
                    self.user.username,
                )
                self.assertEqual(
                    context_with_post.group.title,
                    self.group.title,
                )


class PaginatorViewsTest(TestCase):
    """Paginator показывает правильное кол-во постов на страницах
    'posts:index', 'posts:group_list' и 'posts:profile'"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='slava')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        for i in range(NUMBER_OF_POSTS):
            Post.objects.create(
                text='Тестовый пост',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_views(self):
        templates_url_names = [
            (reverse('posts:index'), 10),
            (reverse('posts:index') + '?page=2', 3),
            (reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ), 10),
            (reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ) + '?page=2', 3),
            (reverse('posts:profile', args={self.user}), 10),
            (reverse('posts:profile', args={self.user}) + '?page=2', 3),
        ]

        for reverse_name, expected_num_posts in templates_url_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(
                    response.context['page_obj']
                ), expected_num_posts)
