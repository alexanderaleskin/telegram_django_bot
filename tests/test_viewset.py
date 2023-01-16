from telegram_django_bot.td_viewset import TelegaViewSet, UserViewSet
from telegram_django_bot.test import TD_TestCase
from telegram_django_bot.routing import telega_reverse
from django.conf import settings

from test_app.models import User
from test_app.views import CategoryViewSet, EntityViewSet


class TestTelegaViewSet(TD_TestCase):
    def setUp(self) -> None:
        user_id = settings.TELEGRAM_TEST_USER_IDS[0]
        self.user = User.objects.create(id=user_id, username=user_id)
        self.cvs = CategoryViewSet(
            telega_reverse('CategoryViewSet'),
            user=self.user,
            bot=self.test_callback_context.bot
        )

    def test_generate_links(self):

        self.assertEqual(
            'cat/cr&name&hat',
            self.cvs.gm_callback_data('create', 'name', 'hat')
        )


class TestUserViewSet(TD_TestCase):
    pass