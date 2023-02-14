from django.test import Client, TestCase
from django.urls import reverse
​
from ..models import Group, Post, User
​
​
​
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
​
    def setUp(self):
        """Создаем клиент автора."""
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(PostCreateFormTests.user)
​
    def test_create_post(self):
        """Проверка создания новой записи в базе данных."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'user': self.user.id
        }
        response = self.authorized_author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile', args=[self.user.username])
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        
        object = Post.objects.last()
        self.assertEqual(object.text, form_data['text'])
        self.assertEqual(object.group, form_data['group'])
        self.assertEqual(object.author.id, form_data['user'])
        