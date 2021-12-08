from django.test import TestCase
from posts.models import Group, Post, User


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.task = Group.objects.create(
            title='Космос',
            slug='Space',
            description='Последние новости о космосе'
        )

    def test_title_group(self):
        """Прверяет правильно ли отображается название группы."""
        group = GroupModelTest.task
        title = group.title
        self.assertEqual(title, GroupModelTest.task.title)


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='Test-author'
        )
        cls.post = Post.objects.create(
            text='t' * 20,
            pub_date='12-04-1961',
            author=cls.user
        )

    def test_text_post(self):
        """Проверяет количество символов поста."""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))
