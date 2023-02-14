import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Post, Group, Comment, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
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
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.not_authorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост1111',
            'group': PostCreateFormTests.group.id,
            'image': PostCreateFormTests.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', args=[PostCreateFormTests.user.username]),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
            ).exists()
        )
        self.assertTrue(form_data['image'], Post.objects.latest('pk').image)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        post = Post.objects.create(
            author=PostCreateFormTests.user,
            text='Тестовый пост',
            group=PostCreateFormTests.group
        )
        new_group = Group.objects.create(
            title='Тестовая группа-2',
            slug='test-slug-2',
        )
        form_data = {
            'text': 'Тестовый пост(измененный)',
            'group': new_group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[post.id]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=[post.id]),
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
            ).exists()
        )
        self.assertFalse(
            Group.objects.filter(
                id=PostCreateFormTests.group.id,
                posts=post.id
            ).exists()
        )

    def test_edit_post_anonymous(self):
        """Неавторизованный пользователь не может создать запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост-2',
            'group': PostCreateFormTests.group.id
        }
        response = self.not_authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=/create/',
        )
        self.assertEqual(Post.objects.count(), posts_count)


class CommentCreateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='user')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user
        )

    def setUp(self):
        self.not_authorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentCreateTests.user)

    def test_create_comment(self):
        """Валидная форма создает запись в Comment."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment', args=[CommentCreateTests.post.id]
            ),
            data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail', args=[CommentCreateTests.post.id]
            ),
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
            )
        )

    def test_create_comment_anonymous(self):
        """Неавторизованный пользователь не может создать запись в Comment."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.not_authorized_client.post(
            reverse(
                'posts:add_comment', args=[CommentCreateTests.post.id]
            ),
            data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login') + f'?next=/posts/'
                                     f'{CommentCreateTests.post.id}/comment/',
        )
        self.assertEqual(Comment.objects.count(), comments_count)
