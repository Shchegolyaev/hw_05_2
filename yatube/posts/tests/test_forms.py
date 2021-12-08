import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Comment, Group, Post, User


class PostCreateFormTests(TestCase):
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
        cls.uploaded = SimpleUploadedFile(
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

        cls.test_group = Group.objects.create(
            title="Тестовая группа",
            slug="test_group",
            description="Тестовая группа"
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            pub_date='13.07.2021',
            author=PostCreateFormTests.user,
            group=PostCreateFormTests.test_group
        )
        cls.form = PostForm()
        cls.kwargs = {"username": PostCreateFormTests.user.username,
                      "post_id": PostCreateFormTests.post.id}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.test_group.id,
            'image': PostCreateFormTests.uploaded
        }
        self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )

        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=form_data['group'],
                text=form_data['text'],
                image=f'posts/{PostCreateFormTests.uploaded.name}'
            ).exists()
        )

    def test_edit_post(self):
        form_data = {
            "text": "Измененный текст",
            "group": PostCreateFormTests.test_group.id
        }
        response = self.authorized_client.post(
            reverse("post_edit", kwargs=PostCreateFormTests.kwargs),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse("post",
                                     kwargs=PostCreateFormTests.kwargs))
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
            ).exists()
        )

    def test_comment_auth_guest(self):
        form_data = {
            "text": "Новый комментарий",
        }
        response = self.authorized_client.post(
            reverse('add_comment', kwargs={
                'username': PostCreateFormTests.user,
                'post_id': PostCreateFormTests.post.id
            }),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse("post",
                                     kwargs=PostCreateFormTests.kwargs))
        self.assertTrue(
            Comment.objects.filter(
                text=form_data["text"],
            ).exists()
        )

        response = self.guest_client.get(
            f'/{PostCreateFormTests.user.username}'
            f'/{PostCreateFormTests.post.id}/add_comment/')
        self.assertEqual(response.status_code, 404)
