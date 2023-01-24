from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@email.com',
            password='password'
        )

        self.client.force_login(self.admin_user)

        self.user = get_user_model().objects.create_user(
            email='user@email.com',
            password='password',
            name='Test User'
        )

    def test_users_list(self):
        logfile = open("test.log", "a")
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)
        print(url, file=logfile)
        print(res.content, file=logfile)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)
        logfile.close()

    def test_edit_user_page(self):
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_create_user(self):
        url = reverse('admin:core_user_add')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
