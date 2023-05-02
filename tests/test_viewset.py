from telegram_django_bot.test import TD_TestCase
from telegram_django_bot.routing import telegram_reverse, RouterCallbackMessageCommandHandler
from django.conf import settings

from test_app.models import Entity, Order, Size, User, Category
from test_app.views import CategoryViewSet, EntityViewSet, OrderViewSet

import unittest
import telegram


class TestTelegramViewSet(TD_TestCase):
    def setUp(self) -> None:
        user_id = settings.TELEGRAM_TEST_USER_IDS[0]
        self.user = User.objects.create(id=user_id, username=user_id)
        self.cvs = CategoryViewSet(
            telegram_reverse('CategoryViewSet'),
            user=self.user,
            bot=self.test_callback_context.bot
        )
        self.evs = EntityViewSet(
            telegram_reverse('EntityViewSet'),
            user=self.user,
            bot=self.test_callback_context.bot
        )
        self.ovs = OrderViewSet(
            telegram_reverse('OrderViewSet'),
            user=self.user,
            bot=self.test_callback_context.bot
        )
        # self.rc_mch = RouterCallbackMessageCommandHandler()
        # self.handle_update = lambda update: self.rc_mch.handle_update(
        #     update, 'some_str', 'some_str', self.test_callback_context
        # )

    def create_size(self):
        size = Size.objects.create(
            name='XL',
        )

        return size

    def create_category(self):
        category = Category.objects.create(
            info='Test',
            name='test'
        )

        return category

    def create_entity(self, category: Category, size: Size):
        entity = Entity.objects.create(
            name='test',
            category_id=category.pk,
            author_id=self.user.id,
            price=322
        )
        entity.sizes.add(size, through_defaults={'amount': 1})
        entity.save()

        return entity

    def create_order(self, entity: Entity):
        order = Order.objects.create(
            info='test',
            status=Order.STATUS_COMPLETED
        )
        order.entities.add(entity)
        order.save()

        return order

    @unittest.skipIf(int(telegram.__version__.split('.')[0]) >= 20, 'tests do not support async')
    def test_category_permission(self):
        category = self.create_category()
        category.name = 'hats'
        category.save()
        category2 = self.create_category()

        start = self.create_update({'text': '/start'})
        res_message = self.handle_update(start)

        action_delete_category = self.create_update(
            res_message.to_dict(),
            {'data': f'cat/de&{category.pk}'}
        )
        res_message = self.handle_update(action_delete_category)
        self.assertEqual(res_message.text, 'Sorry, you do not have permissions to this action.')

        action_delete_category2 = self.create_update(
            res_message.to_dict(),
            {'data': f'cat/de&{category2.pk}'}
        )
        res_message = self.handle_update(action_delete_category2)
        self.assertEqual(res_message.text, f'Are you sure you want to delete Category  #{category2.pk}?')

        start = self.create_update({'text': '/start'})
        res_message = self.handle_update(start)
        
        action_update_name = self.create_update(
            res_message.to_dict(),
            {'data': f'cat/up&{category.pk}&name'}
        )
        res_message = self.handle_update(action_update_name)
        self.assertEqual(res_message.text, 'Sorry, you do not have permissions to this action.')

        action_update_name2 = self.create_update(
            res_message.to_dict(),
            {'data': f'cat/up&{category2.pk}&name'}
        )
        res_message = self.handle_update(action_update_name2)
        self.assertEqual(res_message.text, 'Please, fill the field Category name\n\nmax length 128')

    @unittest.skipIf(int(telegram.__version__.split('.')[0]) >= 20, 'tests do not support async')
    def test_show_list_order_with_foreign_filters(self):
        category = self.create_category()
        size = self.create_size()
        entity_1 = self.create_entity(category, size)
        entity_2 = self.create_entity(category, size)
        order_1 = self.create_order(entity_1)
        order_2 = self.create_order(entity_2)
        
        start = self.create_update({'text': '/start'})
        res_message = self.handle_update(start)

        action_show_list = self.create_update(
            res_message.to_dict(),
            {'data': f'ord/sl&{entity_2.pk}'}
        )
        res_message = self.handle_update(action_show_list)

        buttons = res_message.reply_markup.to_dict()['inline_keyboard']
        self.assertEqual(buttons[0][0]['text'], f'1. Order #{entity_2.pk}')
        self.assertEqual(buttons[0][0]['callback_data'], f'ord/se&{order_2.pk}&{entity_2.pk}')

    def test_create_order_v1(self):
        category = self.create_category()
        size = self.create_size()
        entity = self.create_entity(category, size)

        self.ovs.create('info', 'test')
        self.ovs.create('entities', f'{entity.pk}')
        self.ovs.create('entities', '!GNMS!')

        order_object = Order.objects.get(info='test', entities__pk=entity.pk)
        self.assertEqual(order_object.info, 'test')
        self.assertEqual(order_object.entities.all()[0].pk, entity.pk)

    @unittest.skipIf(int(telegram.__version__.split('.')[0]) >= 20, 'tests do not support async')
    def test_create_order_v2(self):
        category = self.create_category()
        size = self.create_size()
        entity = self.create_entity(category, size)

        start = self.create_update({'text': '/start'})
        res_message = self.handle_update(start)

        action_create_order = self.create_update(
            res_message.to_dict(),
            {'data': 'ord/cr&&info&test'}
        )
        res_message = self.handle_update(action_create_order)

        action_add_entity = self.create_update(
            res_message.to_dict(),
            {'data': f'ord/cr&&entities&{entity.pk}'}
        )
        res_message = self.handle_update(action_add_entity)

        action_confirm_add_entity = self.create_update(
            res_message.to_dict(),
            {'data': 'ord/cr&&entities&!GNMS!'}
        )
        res_message = self.handle_update(action_confirm_add_entity)

        order_object = Order.objects.get(info='test', entities=entity.pk)

        mess = res_message.text.splitlines()
        self.assertEqual(mess[0], 'The Order is created! ')
        self.assertEqual(mess[2], f'Order #{order_object.pk} ')
        self.assertEqual(mess[3], f'Title: {order_object.info}')
        self.assertEqual(mess[4], f'Entities: {entity.name}')

        buttons = res_message.reply_markup.to_dict()['inline_keyboard']
        self.assertEqual(buttons[0][0]['text'], '🔄 Title')
        self.assertEqual(buttons[0][0]['callback_data'], f'ord/up&&{order_object.pk}&info')

        self.assertEqual(buttons[0][1]['text'], '🔄 Entities')
        self.assertEqual(buttons[0][1]['callback_data'], f'ord/up&&{order_object.pk}&entities')

        self.assertEqual(buttons[1][0]['text'], f'❌ Delete #{order_object.pk}')
        self.assertEqual(buttons[1][0]['callback_data'], f'ord/de&&{order_object.pk}')

        self.assertEqual(buttons[2][0]['text'], '🔙 Return to list')
        self.assertEqual(buttons[2][0]['callback_data'], 'ord/sl&')

    def test_delete_entity_v1(self):
        category = self.create_category()
        size = self.create_size()
        entity = self.create_entity(category, size)

        _, (mess, buttons) = self.evs.delete(entity.pk)
        self.assertEqual(mess, f'Are you sure you want to delete Entity  #{entity.pk}?')

        button_1 = buttons[0][0].to_dict()
        self.assertEqual(button_1['text'], '🗑 Yes, delete')
        self.assertEqual(button_1['callback_data'], f'ent/de&{entity.pk}&{entity.pk}')

        button_2 = buttons[1][0].to_dict()
        self.assertEqual(button_2['text'], '🔙 Back')
        self.assertEqual(button_2['callback_data'], f'ent/se&{entity.pk}')

    @unittest.skipIf(int(telegram.__version__.split('.')[0]) >= 20, 'tests do not support async')
    def test_delete_entity_v2(self):
        category = self.create_category()
        size = self.create_size()
        entity = self.create_entity(category, size)

        start = self.create_update({'text': '/start'})
        res_message = self.handle_update(start)

        action_delete_entity = self.create_update(
            res_message.to_dict(),
            {'data': f'ent/de&{entity.pk}'}
        )
        res_message = self.handle_update(action_delete_entity)

        deletion_confirmation = self.create_update(
            res_message.to_dict(),
            {'data': f'ent/de&{entity.pk}&{entity.pk}'}
        )
        res_message = self.handle_update(deletion_confirmation)

        message = res_message.text
        self.assertEqual(message, 'The Entity  #None is successfully deleted.')

        buttons = res_message.reply_markup.to_dict()['inline_keyboard']
        self.assertEqual(buttons[0][0]['text'], '🔙 Return to list')
        self.assertEqual(buttons[0][0]['callback_data'], 'ent/sl')

        entity = Entity.objects.filter(category_id=category.pk).first()
        self.assertEqual(entity, None)

    def test_change_entity_v1(self):
        category = self.create_category()
        size = self.create_size()
        entity = self.create_entity(category, size)
        new_name = 'test_1'

        _, (mess, buttons) = self.evs.change(entity.pk, 'name', new_name)
        self.assertEqual(len(buttons), 5)

        mess = mess.splitlines()
        self.assertEqual(mess[0], 'The field has been updated!')
        self.assertEqual(mess[2], f'Entity #{entity.pk} ')
        self.assertEqual(mess[3], f'<b>Title</b>: {new_name}')
        self.assertEqual(mess[4], f'<b>Category</b>: {entity.category.name}')
        self.assertEqual(mess[5], f'<b>Sizes</b>: {entity.sizes.all()[0].name}')
        self.assertEqual(mess[6], f'<b>Is visable</b>: {entity.is_visable}')
        self.assertEqual(mess[7], f'<b>Price</b>: {entity.price:.2f}')
        self.assertEqual(mess[8], f'<b>Author id</b>: {self.user.id}')

    @unittest.skipIf(int(telegram.__version__.split('.')[0]) >= 20, 'tests do not support async')
    def test_change_entity_v2(self):
        category = self.create_category()
        size = self.create_size()
        entity = self.create_entity(category, size)
        new_name = 'text_1'

        start = self.create_update({'text': '/start'})
        res_message = self.handle_update(start)

        action_change_name_entity = self.create_update(
            res_message.to_dict(),
            {'data': f'ent/up&{entity.pk}&name'}
        )
        res_message = self.handle_update(action_change_name_entity)

        message = res_message.text
        self.assertEqual(message, 'Please, write the value for field Title \n\nmax length 128')

        buttons = res_message.reply_markup.to_dict()['inline_keyboard']
        self.assertEqual(buttons[0][0]['text'], '⬅️ Go back')
        self.assertEqual(buttons[0][0]['callback_data'], f'ent/se&{entity.pk}')

        write_name_for_entity = self.create_update({'text': new_name})
        res_message = self.handle_update(write_name_for_entity)

        mess = res_message.text.splitlines()
        self.assertEqual(mess[0], 'The field has been updated!')
        self.assertEqual(mess[2], f'Entity #{entity.pk} ')
        self.assertEqual(mess[3], f'Title: {new_name}')
        self.assertEqual(mess[4], f'Category: {entity.category.name}')
        self.assertEqual(mess[5], f'Sizes: {entity.sizes.all()[0].name}')
        self.assertEqual(mess[6], f'Is visable: {entity.is_visable}')
        self.assertEqual(mess[7], f'Price: {entity.price:.2f}')
        self.assertEqual(mess[8], f'Author id: {self.user.id}')

    def test_show_list_entity_v1(self):
        category = self.create_category()
        size = self.create_size()
        entity = self.create_entity(category, size)

        _, (mess, buttons) = self.evs.show_list()
        self.assertEqual(len(buttons), 1)

        button_1 = buttons[0][0].to_dict()
        self.assertEqual(button_1['text'], f'1. Entity #{entity.pk}')
        self.assertEqual(button_1['callback_data'], f'ent/se&{entity.pk}')

        mess = mess.splitlines()
        self.assertEqual(mess[0], f'1. Entity #{entity.pk}')
        self.assertEqual(mess[1], f'<b>Title</b>: {entity.name}')
        self.assertEqual(mess[2], f'<b>Category</b>: {entity.category.name}')
        self.assertEqual(mess[3], f'<b>Sizes</b>: {entity.sizes.all()[0].name}')
        self.assertEqual(mess[4], f'<b>Is visable</b>: {entity.is_visable}')
        self.assertEqual(mess[5], f'<b>Price</b>: {entity.price:.2f}')
        self.assertEqual(mess[6], f'<b>Author id</b>: {self.user.id}')

    @unittest.skipIf(int(telegram.__version__.split('.')[0]) >= 20, 'tests do not support async')
    def test_show_list_entity_v2(self):
        category = self.create_category()
        size = self.create_size()
        entity = self.create_entity(category, size)

        start = self.create_update({'text': '/start'})
        res_message = self.handle_update(start)

        action_show_list_entity = self.create_update(
            res_message.to_dict(),
            {'data': 'ent/sl'}
        )
        res_message = self.handle_update(action_show_list_entity)

        buttons = res_message.reply_markup.to_dict()['inline_keyboard']
        self.assertEqual(buttons[0][0]['text'], f'1. Entity #{entity.pk}')
        self.assertEqual(buttons[0][0]['callback_data'], f'ent/se&{entity.pk}')

    def test_show_elem_entity_v1(self):
        category = self.create_category()
        size = self.create_size()
        entity = self.create_entity(category, size)

        _, (mess, buttons) = self.evs.show_elem(entity.pk)
        self.assertEqual(len(buttons), 5)

        mess = mess.splitlines()
        self.assertEqual(mess[0], f'Entity #{entity.pk} ')
        self.assertEqual(mess[1], f'<b>Title</b>: {entity.name}')
        self.assertEqual(mess[2], f'<b>Category</b>: {entity.category.name}')
        self.assertEqual(mess[3], f'<b>Sizes</b>: {entity.sizes.all()[0].name}')
        self.assertEqual(mess[4], f'<b>Is visable</b>: {entity.is_visable}')
        self.assertEqual(mess[5], f'<b>Price</b>: {entity.price:.2f}')
        self.assertEqual(mess[6], f'<b>Author id</b>: {self.user.id}')

        button_1 = buttons[0][0].to_dict()
        self.assertEqual(button_1['text'], '🔄 Title')
        self.assertEqual(button_1['callback_data'], f'ent/up&{entity.pk}&name')

        button_2 = buttons[0][1].to_dict()
        self.assertEqual(button_2['text'], '🔄 Category')
        self.assertEqual(button_2['callback_data'], f'ent/up&{entity.pk}&category')        

        button_3 = buttons[1][0].to_dict()
        self.assertEqual(button_3['text'], '🔄 Sizes')
        self.assertEqual(button_3['callback_data'], f'ent/up&{entity.pk}&sizes')

        button_4 = buttons[1][1].to_dict()
        self.assertEqual(button_4['text'], '🔄 Is visable')
        self.assertEqual(button_4['callback_data'], f'ent/up&{entity.pk}&is_visable')

        button_5 = buttons[2][0].to_dict()
        self.assertEqual(button_5['text'], '🔄 Price')
        self.assertEqual(button_5['callback_data'], f'ent/up&{entity.pk}&price')

        button_6 = buttons[2][1].to_dict()
        self.assertEqual(button_6['text'], '🔄 Author id')
        self.assertEqual(button_6['callback_data'], f'ent/up&{entity.pk}&author_id')

        button_7 = buttons[3][0].to_dict()
        self.assertEqual(button_7['text'], f'❌ Delete #{entity.pk}')
        self.assertEqual(button_7['callback_data'], f'ent/de&{entity.pk}')

        button_8 = buttons[4][0].to_dict()
        self.assertEqual(button_8['text'], '🔙 Return to list')
        self.assertEqual(button_8['callback_data'], 'ent/sl')

    @unittest.skipIf(int(telegram.__version__.split('.')[0]) >= 20, 'tests do not support async')
    def test_show_elem_entity_v2(self):
        category = self.create_category()
        size = self.create_size()
        entity_object = self.create_entity(category, size)

        start = self.create_update({'text': '/start'})
        res_message = self.handle_update(start)

        action_show_elem_entity = self.create_update(
            res_message.to_dict(),
            {'data': f'ent/se&{entity_object.pk}'}
        )
        res_message = self.handle_update(action_show_elem_entity)

        buttons = res_message.reply_markup.to_dict()['inline_keyboard']
        self.assertEqual(buttons[0][0]['text'], '🔄 Title')
        self.assertEqual(buttons[0][0]['callback_data'], f'ent/up&{entity_object.pk}&name')

        self.assertEqual(buttons[0][1]['text'], '🔄 Category')
        self.assertEqual(buttons[0][1]['callback_data'], f'ent/up&{entity_object.pk}&category')

        self.assertEqual(buttons[1][0]['text'], '🔄 Sizes')
        self.assertEqual(buttons[1][0]['callback_data'], f'ent/up&{entity_object.pk}&sizes')

        self.assertEqual(buttons[1][1]['text'], '🔄 Is visable')
        self.assertEqual(buttons[1][1]['callback_data'], f'ent/up&{entity_object.pk}&is_visable')

        self.assertEqual(buttons[2][0]['text'], '🔄 Price')
        self.assertEqual(buttons[2][0]['callback_data'], f'ent/up&{entity_object.pk}&price')

        self.assertEqual(buttons[2][1]['text'], '🔄 Author id')
        self.assertEqual(buttons[2][1]['callback_data'], f'ent/up&{entity_object.pk}&author_id')

        self.assertEqual(buttons[3][0]['text'], f'❌ Delete #{entity_object.pk}')
        self.assertEqual(buttons[3][0]['callback_data'], f'ent/de&{entity_object.pk}')

        self.assertEqual(buttons[4][0]['text'], '🔙 Return to list')
        self.assertEqual(buttons[4][0]['callback_data'], 'ent/sl')

    def test_create_entity_v1(self):
        category = self.create_category()
        size = self.create_size()
        self.evs.create('author_id', 1)
        self.evs.create('sizes', f'{size.pk}')
        self.evs.create('sizes', '!GNMS!')
        self.evs.create('name', 'test')
        self.evs.create('category', category.pk)
        self.evs.create('is_visable', '!NoneNULL!')
        self.evs.create('price', 322)

        entity = Entity.objects.get(
            category_id=category.pk,
            name='test'
        )
        self.assertEqual(entity.name, 'test')
        self.assertEqual(entity.price, 322)
        self.assertEqual(entity.category.pk, category.pk)
        self.assertEqual(entity.author_id, 1)

    @unittest.skipIf(int(telegram.__version__.split('.')[0]) >= 20, 'tests do not support async')
    def test_create_entity_v2(self):
        size_object = self.create_size()
        category_object = self.create_category()

        start = self.create_update({'text': '/start'})
        res_message = self.handle_update(start)

        action_create_entity = self.create_update(
            res_message.to_dict(),
            {'data': 'ent/cr&price&322'}
        )
        res_message = self.handle_update(action_create_entity)

        write_name = self.create_update({'text': 'test'})
        res_message = self.handle_update(write_name)

        add_category_in_entity = self.create_update(
            res_message.to_dict(),
            {'data': f'ent/cr&category&{category_object.pk}'}
        )
        res_message = self.handle_update(add_category_in_entity)

        add_size_in_entity = self.create_update(
            res_message.to_dict(),
            {'data': f'ent/cr&sizes&{size_object.pk}'}
        )
        res_message = self.handle_update(add_size_in_entity)

        choose_size = self.create_update(
            res_message.to_dict(),
            {'data': 'ent/cr&sizes&!GNMS!'}
        )
        res_message = self.handle_update(choose_size)

        leave_blank = self.create_update(
            res_message.to_dict(),
            {'data': 'ent/cr&is_visable&!NoneNULL!'}
        )
        res_message = self.handle_update(leave_blank)

        write_author_id = self.create_update(
            res_message.to_dict(),
            {'data': 'ent/cr&author_id&12'}
        )
        res_message = self.handle_update(write_author_id)

        entity_object = Entity.objects.get(
            category_id=category_object.pk,
            name='test'
        )

        buttons = res_message.reply_markup.to_dict()['inline_keyboard']
        self.assertEqual(len(buttons), 5)

        self.assertEqual(buttons[0][0]['text'], '🔄 Title')
        self.assertEqual(buttons[0][0]['callback_data'], f'ent/up&{entity_object.pk}&name')

        self.assertEqual(buttons[0][1]['text'], '🔄 Category')
        self.assertEqual(buttons[0][1]['callback_data'], f'ent/up&{entity_object.pk}&category')

        self.assertEqual(buttons[1][0]['text'], '🔄 Sizes')
        self.assertEqual(buttons[1][0]['callback_data'], f'ent/up&{entity_object.pk}&sizes')

        self.assertEqual(buttons[1][1]['text'], '🔄 Is visable')
        self.assertEqual(buttons[1][1]['callback_data'], f'ent/up&{entity_object.pk}&is_visable')

        self.assertEqual(buttons[2][0]['text'], '🔄 Price')
        self.assertEqual(buttons[2][0]['callback_data'], f'ent/up&{entity_object.pk}&price')

        self.assertEqual(buttons[2][1]['text'], '🔄 Author id')
        self.assertEqual(buttons[2][1]['callback_data'], f'ent/up&{entity_object.pk}&author_id')

        self.assertEqual(buttons[3][0]['text'], f'❌ Delete #{entity_object.pk}')
        self.assertEqual(buttons[3][0]['callback_data'], f'ent/de&{entity_object.pk}')

        self.assertEqual(buttons[4][0]['text'], '🔙 Return to list')
        self.assertEqual(buttons[4][0]['callback_data'], 'ent/sl')

    def test_create_category_v1(self):
        self.cvs.create('name', 'test')
        category = Category.objects.get(name='test')

        self.assertEqual(category.name, 'test')

    @unittest.skipIf(int(telegram.__version__.split('.')[0]) >= 20, 'tests do not support async')
    def test_create_category_v2(self):
        category_name = 'шапки'

        start_send = self.create_update({'text': '/start'})
        res_message = self.handle_update(start_send)

        action_add_category = self.create_update(
            res_message.to_dict(),
            {'data': f'cat/cr&name&{category_name}'}
        )
        res_message = self.handle_update(action_add_category)

        category_object = Category.objects.get(name=category_name)
        self.assertEqual(category_name, category_object.name)

        buttons = res_message.reply_markup.to_dict()['inline_keyboard']
        self.assertEqual(len(buttons), 3)

        button_1, button_2, button_3 = buttons
        self.assertEqual(button_1[0]['text'], '🔄 Category name')
        self.assertEqual(button_1[0]['callback_data'], f'cat/up&{category_object.pk}&name')

        self.assertEqual(button_2[0]['text'], f'❌ Delete #{category_object.pk}')
        self.assertEqual(button_2[0]['callback_data'], f'cat/de&{category_object.pk}')

        self.assertEqual(button_3[0]['text'], '🔙 Return to list')
        self.assertEqual(button_3[0]['callback_data'], 'cat/sl')

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
        _, (mess, buttons) = self.cvs.gm_no_elem(model.pk)

        self.assertEqual(mess, f'The Category {model.pk} has not been found 😱 \nPlease try again from the beginning.')

    def test_gm_show_elem_create_buttons(self):
        model = self.create_category()
        button_1, button_2, button_3 = self.cvs.gm_show_elem_create_buttons(model)

        button_1 = button_1[0].to_dict()
        self.assertEqual(button_1['text'], '🔄 Category name')
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

        self.assertEqual(mess, f'<b>Category name</b>: {model.name}\n')

    def test_gm_value_str(self):
        model = self.create_category()
        value = self.cvs.gm_value_str(model, model.info, 'info')

        self.assertEqual(value, model.info)

    def test_gm_show_list_elem_info(self):
        model = self.create_category()
        mess = self.cvs.gm_show_list_elem_info(model, 1)

        self.assertEqual(mess, f'1. Category #{model.pk}\n<b>Category name</b>: {model.name}\n\n\n')

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
        _, (mess, buttons) = self.cvs.gm_success_created(model.pk)
        button_1, button_2, button_3 = buttons

        self.assertEqual(mess, f'The Category is created! \n\nCategory #{model.pk} \n<b>Category name</b>: {model.name}\n')
        
        button_1 = button_1[0].to_dict()
        self.assertEqual(button_1['text'], '🔄 Category name')
        self.assertEqual(button_1['callback_data'], f'cat/up&{model.pk}&name')

        button_2 = button_2[0].to_dict()
        self.assertEqual(button_2['text'], f'❌ Delete #{model.pk}')
        self.assertEqual(button_2['callback_data'], f'cat/de&{model.pk}')

        button_3 = button_3[0].to_dict()
        self.assertEqual(button_3['text'], '🔙 Return to list')
        self.assertEqual(button_3['callback_data'], 'cat/sl')

    def test_gm_value_error(self):
        _, (mess, buttons) = self.cvs.gm_value_error('info', 'Error')
        button_1, button_2 = buttons

        button_1 = button_1[0].to_dict()
        self.assertEqual(button_1['text'], 'Leave blank')
        self.assertEqual(button_1['callback_data'], 'cat/cr&info&!NoneNULL!')

        button_2 = button_2[0].to_dict()
        self.assertEqual(button_2['text'], 'Cancel adding')
        self.assertEqual(button_2['callback_data'], 'cat/sl')

        self.assertEqual(mess, 'While adding Info the next errors were occurred: Error\n\nPlease, write the value for field Info \n\nextra info about category\n\n')

    def test_gm_self_variant(self):
        _, (mess, buttons) = self.cvs.gm_self_variant('info')
        button_1, button_2 = buttons

        button_1 = button_1[0].to_dict()
        self.assertEqual(button_1['text'], 'Leave blank')
        self.assertEqual(button_1['callback_data'], 'cat/cr&info&!NoneNULL!')

        button_2 = button_2[0].to_dict()
        self.assertEqual(button_2['text'], 'Cancel adding')
        self.assertEqual(button_2['callback_data'], 'cat/sl')

        self.assertEqual(mess, 'Please, write the value for field Info \n\nextra info about category\n\n')


@unittest.skipIf(int(telegram.__version__.split('.')[0]) >= 20, 'tests do not support async')
class TestUserViewSet(TD_TestCase):
    def setUp(self) -> None:
        user_id = settings.TELEGRAM_TEST_USER_IDS[0]
        self.user = User.objects.create(id=user_id, username=user_id)
        
        self.rc_mch = RouterCallbackMessageCommandHandler()
        self.handle_update = lambda update: self.rc_mch.handle_update(
            update, 'some_str', 'some_str', self.test_callback_context
        )

    def test_show_elem(self):
        start = self.create_update({'text': '/start'})
        res_message = self.handle_update(start)

        action_show_settings = self.create_update(
            res_message.to_dict(),
            {'data': 'us/se'}
        )
        res_message = self.handle_update(action_show_settings)

        buttons = res_message.reply_markup.to_dict()['inline_keyboard']
        self.assertEqual(buttons[0][0]['text'], '🔄 Timezone')
        self.assertEqual(buttons[0][0]['callback_data'], f'us/up&{self.user.id}&timezone')
        self.assertEqual(buttons[0][1]['text'], '🔄 Language')
        self.assertEqual(buttons[0][1]['callback_data'], f'us/up&{self.user.id}&telegram_language_code')
        self.assertEqual(res_message.text, 'Timezone: +3 UTC\nLanguage: English')

    def test_change_language(self):
        start = self.create_update({'text': '/start'})
        res_message = self.handle_update(start)

        action_change_timezone = self.create_update(
            res_message.to_dict(),
            {'data': f'us/up&{self.user.id}&telegram_language_code'}
        )
        res_message = self.handle_update(action_change_timezone)
        
        message = res_message.text
        buttons = res_message.reply_markup.to_dict()['inline_keyboard']

        self.assertEqual(message, 'Please, fill the field Language')

        self.assertEqual(buttons[0][0]['text'], '✅ English')
        self.assertEqual(buttons[0][0]['callback_data'], f'us/up&{self.user.id}&telegram_language_code&en')

        self.assertEqual(buttons[1][0]['text'], 'German')
        self.assertEqual(buttons[1][0]['callback_data'], f'us/up&{self.user.id}&telegram_language_code&de')

        self.assertEqual(buttons[2][0]['text'], 'Russian')
        self.assertEqual(buttons[2][0]['callback_data'], f'us/up&{self.user.id}&telegram_language_code&ru')

        self.assertEqual(buttons[3][0]['text'], '⬅️ Go back')
        self.assertEqual(buttons[3][0]['callback_data'], f'us/se&{self.user.id}')
