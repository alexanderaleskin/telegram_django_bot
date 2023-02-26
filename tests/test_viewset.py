from telegram_django_bot.td_viewset import TelegramViewSet
from telegram_django_bot.user_viewset import UserViewSet
from telegram_django_bot.test import TD_TestCase
from telegram_django_bot.routing import telega_reverse
from django.conf import settings

from test_app.models import User, Category
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

    def create_category(self):
        category = Category.objects.create(
            info='Test',
            name='test'
        )

        return category

    def test_generate_links(self):
        self.assertEqual(
            'cat/cr&name&hat',
            self.cvs.gm_callback_data('create', 'name', 'hat')
        )

    def test_gm_delete_getting_confirmation(self):
        model = self.create_category()
        mess, buttons = self.cvs.gm_delete_getting_confirmation(model)
        button_1, button_2 = buttons

        button_1 = button_1[0].to_dict()
        self.assertEqual(button_1['text'], '🗑 Yes, delete')
        self.assertEqual(button_1['callback_data'], f'cat/de&{model.pk}&{model.pk}')

        button_2 = button_2[0].to_dict()
        self.assertEqual(button_2['text'], '🔙 Back')
        self.assertEqual(button_2['callback_data'], f'cat/se&{model.pk}')

        self.assertEqual(mess, 'Are you sure you want to delete Category  #1?')

    def test_gm_delete_successfully(self):
        model = self.create_category()
        mess, button = self.cvs.gm_delete_successfully(model)

        button = button[0][0].to_dict()
        self.assertEqual(button['text'], '🔙 Return to list')
        self.assertEqual(button['callback_data'], 'cat/sl')

        self.assertEqual(mess, f'The Category  #{model.pk} is successfully deleted.')

    def test_gm_no_elem(self):
        model = self.create_category()
        __, (mess, buttons) = self.cvs.gm_no_elem(model.pk)

        self.assertEqual(mess, f'The Category {model.pk} has not been found 😱 \nPlease try again from the beginning.')

    def test_gm_show_elem_create_buttons(self):
        model = self.create_category()
        button_1, button_2, button_3 = self.cvs.gm_show_elem_create_buttons(model)

        button_1 = button_1[0].to_dict()
        self.assertEqual(button_1['text'], '🔄 Название категории')
        self.assertEqual(button_1['callback_data'], f'cat/up&{model.pk}&name')

        button_2 = button_2[0].to_dict()
        self.assertEqual(button_2['text'], f'❌ Delete #{model.pk}')
        self.assertEqual(button_2['callback_data'], f'cat/de&{model.pk}')

        button_3 = button_3[0].to_dict()
        self.assertEqual(button_3['text'], '🔙 Return to list')
        self.assertEqual(button_3['callback_data'], 'cat/sl')

    def test_gm_show_elem_or_list_fields(self):
        model = self.create_category()
        mess = self.cvs.gm_show_elem_or_list_fields(model)

        self.assertEqual(mess, f'<b>Название категории</b>: {model.name}\n')

    def test_gm_value_str(self):
        model = self.create_category()
        value = self.cvs.gm_value_str(model, model.info, 'info')

        self.assertEqual(value, model.info)

    def test_gm_show_list_elem_info(self):
        model = self.create_category()
        mess = self.cvs.gm_show_list_elem_info(model, 1)

        self.assertEqual(mess, f'1. Category #{model.pk}\n<b>Название категории</b>: {model.name}\n\n\n')

    def test_gm_show_list_button_names(self):
        model = self.create_category()
        mess = self.cvs.gm_show_list_button_names(1, model)

        self.assertEqual(mess, f'1. Category #{model.pk}')

    def test_gm_show_list_create_pagination(self):
        button_1, button_2 = self.cvs.gm_show_list_create_pagination(0, 10, 1, 2, 5)[0]

        button_1 = button_1.to_dict()
        self.assertEqual(button_1['text'], '◀️️️')
        self.assertEqual(button_1['callback_data'], 'cat/sl&-1')

        button_2 = button_2.to_dict()
        self.assertEqual(button_2['text'], '️▶️️')
        self.assertEqual(button_2['callback_data'], 'cat/sl&1')

    def test_gm_success_created(self):
        model = self.create_category()
        __, (mess, buttons) = self.cvs.gm_success_created(model.pk)
        button_1, button_2, button_3 = buttons

        self.assertEqual(mess, f'The Category is created! \n\nCategory #{model.pk} \n<b>Название категории</b>: {model.name}\n')

        button_1 = button_1[0].to_dict()
        self.assertEqual(button_1['text'], '🔄 Название категории')
        self.assertEqual(button_1['callback_data'], f'cat/up&{model.pk}&name')

        button_2 = button_2[0].to_dict()
        self.assertEqual(button_2['text'], f'❌ Delete #{model.pk}')
        self.assertEqual(button_2['callback_data'], f'cat/de&{model.pk}')

        button_3 = button_3[0].to_dict()
        self.assertEqual(button_3['text'], '🔙 Return to list')
        self.assertEqual(button_3['callback_data'], 'cat/sl')

    def test_gm_value_error(self):
        __, (mess, buttons) = self.cvs.gm_value_error('info', 'Error')
        button_1, button_2 = buttons

        button_1 = button_1[0].to_dict()
        self.assertEqual(button_1['text'], 'Leave blank')
        self.assertEqual(button_1['callback_data'], 'cat/cr&info&!NoneNULL!')

        button_2 = button_2[0].to_dict()
        self.assertEqual(button_2['text'], 'Cancel adding')
        self.assertEqual(button_2['callback_data'], 'cat/sl')

        self.assertEqual(mess, 'While adding Информация the next errors were occurred: Error\n\nPlease, write the value for field Информация \n\nextra info about category\n\n')

    def test_gm_self_variant(self):
        __, (mess, buttons) = self.cvs.gm_self_variant('info')
        button_1, button_2 = buttons

        button_1 = button_1[0].to_dict()
        self.assertEqual(button_1['text'], 'Leave blank')
        self.assertEqual(button_1['callback_data'], 'cat/cr&info&!NoneNULL!')

        button_2 = button_2[0].to_dict()
        self.assertEqual(button_2['text'], 'Cancel adding')
        self.assertEqual(button_2['callback_data'], 'cat/sl')

        self.assertEqual(mess, 'Please, write the value for field Информация \n\nextra info about category\n\n')


class TestUserViewSet(TD_TestCase):
    pass
