from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            first_name='Leonid',
            last_name='Vladimorov',
            username='leonid',
            email='lev@yandex.ru'
        )
        cls.user2 = User.objects.create(
            username='sergey'
        )

        cls.group = Group.objects.create(
            title='Насекомые',
            slug='bags',
            description='Test-group'
        )

        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            pub_date='13.07.2021',
            author=StaticURLTests.user,
            group=StaticURLTests.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.user2)
        self.authorized_client.force_login(StaticURLTests.user)
        cache.clear()

    def test_guest_client_status_code(self):
        """Приходит ожидаемый ответ для не авторизованного пользователя."""
        adress_names = {
            '/': 200,
            f'/group/{StaticURLTests.group.slug}/': 200,
            f'/{StaticURLTests.user.username}/{StaticURLTests.post.id}'
            '/edit/': 302,
        }
        for adress, code in adress_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, code)

    def test_authorized_client_status_code(self):
        """Приходит ожидаемый ответ для авторизованного пользователя."""
        adress_names = {
            '/new/': 200,
            f'/{StaticURLTests.user.username}/': 200,
            f'/{StaticURLTests.user.username}/{StaticURLTests.post.id}/': 200,
            f'/{StaticURLTests.user.username}/{StaticURLTests.post.id}'
            '/edit/': 200,
            f'/{StaticURLTests.user2.username}/{StaticURLTests.post.id}'
            '/edit/': 302,
        }
        for adress, code in adress_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'index.html': '/',
            'group.html': f'/group/{StaticURLTests.group.slug}/',
            'form.html': '/new/',

        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_404_status_code(self):
        response = self.authorized_client.get('/none/')
        self.assertEqual(response.status_code, 404)
