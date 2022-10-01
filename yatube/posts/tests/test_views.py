import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.core.cache import cache

from ..models import Post, Group, User, Follow
from ..forms import PostForm
from ..utils import POSTS_ON_PAGE


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.user = User.objects.create_user(username='user')

        cls.user_follower = User.objects.create_user(username='user_follower')

        cls.user_not_follower = User.objects.create_user(
            username='user_not_follower'
        )

        Follow.objects.create(user=cls.user_follower, author=cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
        )

        posts = [
            Post(
                author=cls.user,
                text='Тестовый пост' + str(i),
                group=cls.group,
                image=uploaded
            )
            for i in range(13)
        ]

        Post.objects.bulk_create(posts)
        cls.post = Post.objects.latest('id')

        cls.url_index = '/'
        cls.url_group_list = f'/group/{cls.group.slug}/'
        cls.url_group_list2 = f'/group/{cls.group2.slug}/'
        cls.url_profile = f'/profile/{cls.user}/'
        cls.url_post_detail = f'/posts/{cls.post.pk}/'
        cls.url_post_create = '/create/'
        cls.url_post_edit = f'/posts/{cls.post.pk}/edit/'
        cls.url_follow_index = '/follow/'
        cls.url_follow = f'/profile/{cls.user}/follow/'
        cls.url_unfollow = f'/profile/{cls.user}/unfollow/'

        cls.all_urls = (
            cls.url_index,
            cls.url_group_list,
            cls.url_profile,
            cls.url_post_detail,
            cls.url_post_create,
            cls.url_post_edit,
            cls.url_follow_index,
            cls.url_follow,
            cls.url_unfollow
        )

        cls.pages_with_content_urls = [
            cls.url_index,
            cls.url_group_list,
            cls.url_profile,
            cls.url_post_detail,
            cls.url_follow_index
        ]

        cls.pages_with_paginator = [
            cls.url_index,
            cls.url_group_list,
            cls.url_profile,
            cls.url_follow_index
        ]

        cls.urls_template = [
            (cls.url_index, 'posts/index.html'),
            (cls.url_group_list, 'posts/group_list.html'),
            (cls.url_profile, 'posts/profile.html'),
            (cls.url_post_detail, 'posts/post_detail.html'),
            (cls.url_post_create, 'posts/create_post.html'),
            (cls.url_post_edit, 'posts/create_post.html'),
            (cls.url_follow_index, 'posts/follow.html')
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()

        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)

        self.user_follower = Client()
        self.user_follower.force_login(PostsURLTests.user_follower)

        self.user_not_follower = Client()
        self.user_not_follower.force_login(PostsURLTests.user_not_follower)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in PostsURLTests.urls_template:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_page_show_correct_context(self):
        """Функция проверки правильности контекста"""
        for url in PostsURLTests.pages_with_content_urls:
            with self.subTest(url=url):
                response = self.user_follower.get(url)
                if url == PostsURLTests.url_post_detail:
                    object = response.context['post']
                else:
                    object = response.context['page_obj'][0]
                self.assertEqual(object.text, PostsURLTests.post.text)
                self.assertEqual(object.pub_date, PostsURLTests.post.pub_date)
                self.assertEqual(object.author, PostsURLTests.post.author)
                self.assertEqual(object.group, PostsURLTests.post.group)
                self.assertEqual(object.image, PostsURLTests.post.image)

        response = self.authorized_client.get(PostsURLTests.url_group_list2)
        objects = response.context['page_obj']
        self.assertEqual(len(objects), 0)

        response = self.user_not_follower.get(PostsURLTests.url_follow_index)
        objects = response.context['page_obj']
        self.assertEqual(len(objects), 0)

    def test_create_post_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(PostsURLTests.url_post_create)
        form = response.context['form']
        self.assertIsInstance(form, PostForm)

    def test_create_post_for_edit_correct_context(self):
        """
        Шаблон create_post для редактирования поста
        сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(PostsURLTests.url_post_edit)
        form = response.context['form']
        self.assertIsInstance(form, PostForm)
        self.assertEqual(form.instance, PostsURLTests.post)

    def test_pages_with_paginator(self):
        """Корректность отображения количества постов на странице."""
        posts_on_second_page = Post.objects.count() - POSTS_ON_PAGE
        page_posts = [(1, POSTS_ON_PAGE), (2, posts_on_second_page)]

        for url in PostsURLTests.pages_with_paginator:
            for page, posts in page_posts:
                with self.subTest(url=url):
                    response = self.user_follower.get(url, {'page': page})
                    posts_on_page = len(response.context['page_obj'])
                    self.assertEqual(posts_on_page, posts)
                    cache.clear()

    def test_cache_on_index(self):
        """Тестирование работе кеширования главной страницы."""
        response = self.authorized_client.get(PostsURLTests.url_index)

        obj_before_del = response.context['page_obj'][0]
        content_before_del = response.content
        Post.objects.filter(id=obj_before_del.id).delete()

        response = self.authorized_client.get(PostsURLTests.url_index)
        content_after_del = response.content
        self.assertEqual(content_after_del, content_before_del)

        cache.clear()
        response = self.authorized_client.get(PostsURLTests.url_index)
        obj_after_del_cache_clear = response.context['page_obj'][0]
        self.assertNotEqual(obj_before_del, obj_after_del_cache_clear)

    def test_following(self):
        """Тестирование подписок и отписок."""
        self.user_not_follower.get(PostsURLTests.url_follow)
        self.assertEqual(
            len(
                Follow.objects.filter(
                    user=PostsURLTests.user_not_follower,
                    author=PostsURLTests.user
                )
            ), 1
        )

        self.user_not_follower.get(PostsURLTests.url_unfollow)
        self.assertNotEqual(
            len(
                Follow.objects.filter(
                    user=PostsURLTests.user_not_follower,
                    author=PostsURLTests.user
                )
            ), 1
        )
