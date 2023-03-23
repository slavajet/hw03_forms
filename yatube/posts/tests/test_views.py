from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Post, Group

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
        post_list = []
        for i in range(NUMBER_OF_POSTS):
            post = Post(
                text=f'Тестовый пост-{i}',
                author=cls.user,
                group=cls.group,
            )
            post_list.append(post)
        Post.objects.bulk_create(post_list)
        cls.posts = Post.objects.all()
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """Во view-функциях используются правильные html-шаблоны"""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': PostModelTest.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': PostModelTest.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': PostModelTest.posts[1].id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': PostModelTest.posts[1].id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Cловарь contex соответствует ожиданиям на страницах:
        'posts:index', 'posts:group_list' и 'posts:profile'"""
        templates_url_names = [
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': PostModelTest.group.slug}
            ),
            reverse(
                'posts:profile', kwargs={'username': PostModelTest.user}
            ),
        ]
        for reverse_name in templates_url_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                self.assertEqual(response.status_code, 200)
                self.assertIn('page_obj', response.context)
                self.assertEqual(first_object.text, self.posts[0].text)
                self.assertEqual(
                    first_object.author.username,
                    self.user.username
                )
                self.assertEqual(first_object.group.title, PostModelTest.group.title)

    def test_post_detail_show_correct_context(self):
        """Cловарь contex соответствует ожиданиям на странице 'post_detail'"""
        response = self.client.get(reverse('posts:post_detail', args={PostModelTest.posts[1].id}))
        first_object = response.context['full_post']
        self.assertEqual(response.status_code, 200)
        self.assertEqual(first_object.text, PostModelTest.posts[1].text)
        self.assertEqual(first_object.author.username, PostModelTest.user.username)
        self.assertEqual(first_object.group.title, PostModelTest.group.title)

    def test_post_create_show_correct_context(self):
        """Cловарь contex соответствует ожиданиям на странице 'post_create'"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form = response.context['form']
        self.assertIsInstance(form, PostForm)
        self.assertEqual(response.status_code, 200)
        for field_name, field_type in self.form_fields.items():
            self.assertIsInstance(form.fields[field_name], field_type)

    def test_post_edit_show_correct_context(self):
        """Cловарь contex соответствует ожиданиям на странице 'post_edit'"""
        response = self.authorized_client.get(reverse('posts:post_edit', args=[PostModelTest.posts[1].id]))
        form = response.context['form']
        self.assertIsInstance(form, PostForm)
        self.assertEqual(form.instance, PostModelTest.posts[1])
        self.assertEqual(response.status_code, 200)
        for field_name, field_type in self.form_fields.items():
            self.assertIsInstance(form.fields[field_name], field_type)

    def test_paginator(self):
        """Paginator показывает правильное кол-во постов на страницах
        'posts:index', 'posts:group_list' и 'posts:profile'"""
        templates_url_names = [
            (reverse('posts:index'), 10),
            (reverse('posts:index') + '?page=2', 3),
            (reverse(
                'posts:group_list', kwargs={'slug': PostModelTest.group.slug}
            ), 10),
            (reverse(
                'posts:group_list', kwargs={'slug': PostModelTest.group.slug}
            ) + '?page=2', 3),
            (reverse('posts:profile', args={PostModelTest.user}), 10),
            (reverse('posts:profile', args={PostModelTest.user}) + '?page=2', 3),
        ]

        for reverse_name, expected_num_posts in templates_url_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(
                    response.context['page_obj']
                ), expected_num_posts)
