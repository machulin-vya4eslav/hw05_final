from http import HTTPStatus

from django.test import TestCase, Client
from django.core.cache import cache

from ..models import Post, Group, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

        cls.url_index = '/'
        cls.url_group_list = f'/group/{cls.group.slug}/'
        cls.url_profile = f'/profile/{cls.user}/'
        cls.url_post_detail = f'/posts/{cls.post.pk}/'
        cls.url_post_create = '/create/'
        cls.url_post_edit = f'/posts/{cls.post.pk}/edit/'
        cls.url_404 = '/non-existing-page/'

        cls.public_urls = (
            cls.url_index,
            cls.url_group_list,
            cls.url_profile,
            cls.url_post_detail
        )

        cls.private_urls = (
            cls.url_post_create,
            cls.url_post_edit
        )

        cls.urls_template = [
            (cls.url_index, 'posts/index.html'),
            (cls.url_group_list, 'posts/group_list.html'),
            (cls.url_profile, 'posts/profile.html'),
            (cls.url_post_detail, 'posts/post_detail.html'),
            (cls.url_post_create, 'posts/create_post.html'),
            (cls.url_post_edit, 'posts/create_post.html'),
            (cls.url_404, 'core/404.html')
        ]

    def setUp(self):
        cache.clear()

        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)

        self.author_client = Client()
        self.author_client.force_login(PostsURLTests.author)

    def test_urls_public(self):
        """Проверяем доступность общедоступных страниц"""
        for url in PostsURLTests.public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_private(self):
        """Проверяем доступность приватных страниц"""
        for url in PostsURLTests.private_urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_urls_redirect_not_author(self):
        """Проверяем редирект с /posts/<post_id>/edit/ для не авторов поста"""
        response = self.authorized_client.get(PostsURLTests.url_post_edit)
        self.assertRedirects(response, PostsURLTests.url_post_detail)

    def test_urls_redirect_anonymous(self):
        """Проверяем редиректы для неавторизованного пользователя"""
        templates_url_names = [
            (url, f'/auth/login/?next={url}')
            for url in PostsURLTests.private_urls
        ]
        for url, status in templates_url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, status)

    def test_edit_urls_exists_at_desired_location_authorized_author(self):
        """Проверяем доступность /posts/<post_id>/edit/ для автора"""
        response = self.author_client.get(PostsURLTests.url_post_edit)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in PostsURLTests.urls_template:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)
