import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Follow, Group, Post

User = get_user_model()


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

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
            author=TaskPagesTests.user,
            group=TaskPagesTests.group,
            image=uploaded
        )
        cls.kwargs = {"username": TaskPagesTests.user.username,
                      "post_id": TaskPagesTests.post.id}
        cls.kwargs_group_posts = {'slug': TaskPagesTests.group.slug}
        cls.kwargs_profile = {'username': TaskPagesTests.user.username}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskPagesTests.user2)
        self.authorized_client.force_login(TaskPagesTests.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group_posts',
                                  kwargs=TaskPagesTests.kwargs_group_posts),
            'form.html': reverse('new_post'),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        first_object = response.context['page'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        self.assertEqual(post_text_0, TaskPagesTests.post.text)
        self.assertEqual(post_author_0, TaskPagesTests.user.username)

    def test_group_show_correct_context(self):
        """Шаблон task_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('group_posts', kwargs=TaskPagesTests.kwargs_group_posts))
        self.assertEqual(response.context['group'].title,
                         TaskPagesTests.group.title)
        self.assertEqual(response.context['group'].slug,
                         TaskPagesTests.group.slug)
        self.assertEqual(response.context['group'].description,
                         TaskPagesTests.group.description)

    def test_form_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон form сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('post_edit',
                                              kwargs=TaskPagesTests.kwargs))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        self.assertIsInstance(response.context['form'], PostForm)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('profile', kwargs=TaskPagesTests.kwargs_profile))
        first_object = response.context['page'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        self.assertEqual(post_text_0, TaskPagesTests.post.text)
        self.assertEqual(post_author_0, TaskPagesTests.user.username)

    def test_post_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('post', kwargs=TaskPagesTests.kwargs))
        first_object = response.context['post']
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        self.assertEqual(post_text_0, TaskPagesTests.post.text)
        self.assertEqual(post_author_0, TaskPagesTests.user.username)

    def test_image_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""

        form_fields = {
            'index': '',
            'profile': TaskPagesTests.kwargs_profile,
            'group_posts': TaskPagesTests.kwargs_group_posts
        }

        for name, kwargs in form_fields.items():
            response = self.authorized_client.get(
                reverse(name, kwargs=kwargs))
            with self.subTest(name=name):
                first_object = response.context['page'][0]
                post_image_0 = first_object.image
                self.assertEqual(post_image_0, TaskPagesTests.post.image)

    def test_post_image_correct_context(self):
        response = self.authorized_client.get(
            reverse('post', kwargs=TaskPagesTests.kwargs))
        first_object = response.context['post']
        post_image_0 = first_object.image
        self.assertEqual(post_image_0, TaskPagesTests.post.image)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            username='leonid',
        )

        cls.user2 = User.objects.create(
            username='sergey'
        )

        cls.user3 = User.objects.create(
            username='andrey'
        )

        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            pub_date='13.07.2021',
            author=FollowTests.user,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(FollowTests.user)
        self.authorized_client.force_login(FollowTests.user2)

    def test_follow(self):
        count = Follow.objects.count()

        self.authorized_client.post(
            reverse('profile_follow',
                    kwargs={'username': FollowTests.user}))
        self.assertEqual(Follow.objects.count(), count + 1)

    def test_unfollow(self):
        count = Follow.objects.count()
        self.authorized_client.post(
            reverse('profile_unfollow',
                    kwargs={'username': FollowTests.user}))
        self.assertEqual(Follow.objects.count(), count)

    def test_post_for_follow_unfollow(self):
        self.authorized_client.post(
            reverse('profile_follow',
                    kwargs={'username': FollowTests.user}))

        response = self.authorized_client.get(
            reverse('follow_index'))
        first_object = response.context['page'][0]
        text_0 = first_object.text
        author_0 = first_object.author
        self.assertEqual(text_0, FollowTests.post.text)
        self.assertEqual(author_0, FollowTests.post.author)

        self.authorized_client.post(
            reverse('profile_unfollow',
                    kwargs={'username': FollowTests.user}))
        response = self.authorized_client.get(
            reverse('follow_index'))
        first_object = response.context['page']
        self.assertFalse(first_object)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            first_name='Leonid',
            last_name='Vladimorov',
            username='leonid',
            email='lev@yandex.ru'
        )

        cls.group = Group.objects.create(
            title='Насекомые',
            slug='bags',
            description='Test-group'
        )
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
        posts = []
        for i in range(13):
            posts.append(Post(text=f'Тестовый текст поста {i}',
                              pub_date='13.07.2021',
                              author=PaginatorViewsTest.user,
                              group=PaginatorViewsTest.group))
        Post.objects.bulk_create(posts)

    def setUp(self):
        cache.clear()

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(len(response.context['page']), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context['page']), 3)


class CreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            first_name='Leonid',
            last_name='Vladimorov',
            username='leonid',
            email='lev@yandex.ru'
        )

        cls.group = Group.objects.create(
            title='Насекомые',
            slug='bags',
            description='Test-group'
        )

        cls.group2 = Group.objects.create(
            title='Test2',
            slug='slug-test2',
            description='Test-group2'
        )

        cls.post1 = Post.objects.create(
            text='Тестовый текст поста',
            pub_date='13.07.2021',
            author=CreateFormTest.user,
            group=CreateFormTest.group
        )
        cls.kwargs_group = {'slug': CreateFormTest.group.slug}
        cls.kwargs_group2 = {'slug': CreateFormTest.group2.slug}

    def setUp(self):
        self.user = User.objects.create_user(username='sergey')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_check_post_in_index(self):
        response = self.authorized_client.get(
            reverse('index'))
        first_object = response.context['page'][0]
        post_text = first_object.text
        post_group = first_object.group

        self.assertEqual(post_text, CreateFormTest.post1.text)
        self.assertEqual(post_group.title, CreateFormTest.group.title)

    def test_check_post_in_group(self):
        response = self.authorized_client.get(
            reverse('group_posts', kwargs=CreateFormTest.kwargs_group)
        )
        self.assertEqual(response.context['group'].title,
                         CreateFormTest.group.title)
        self.assertEqual(response.context['group'].slug,
                         CreateFormTest.group.slug)
        self.assertEqual(response.context['group'].description,
                         CreateFormTest.group.description)

        first_object = response.context['page'][0]
        post_text = first_object.text
        post_group = first_object.group

        self.assertEqual(post_text, CreateFormTest.post1.text)
        self.assertEqual(post_group.title, CreateFormTest.group.title)

        response = self.authorized_client.get(
            reverse('group_posts', kwargs=CreateFormTest.kwargs_group2)
        )
        self.assertFalse(len(response.context['page']))


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            first_name='Leonid',
            last_name='Vladimorov',
            username='leonid',
            email='lev@yandex.ru'
        )

        cls.group = Group.objects.create(
            title='Насекомые',
            slug='bags',
            description='Test-group'
        )

        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            pub_date='13.07.2021',
            author=CacheTest.user,
            group=CacheTest.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CacheTest.user)
        cache.clear()

    def test_cache_index(self):
        response = self.authorized_client.get(
            reverse('index'))
        CacheTest.post.delete()
        self.assertTrue(response.context['page'][0])

        cache.clear()

        response = self.authorized_client.get(
            reverse('index'))
        self.assertFalse(response.context['page'])


class AboutTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            first_name='Leonid',
            last_name='Vladimorov',
            username='leonid',
            email='lev@yandex.ru'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='sergey')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_about_author_(self):
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_about_tech_(self):
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
