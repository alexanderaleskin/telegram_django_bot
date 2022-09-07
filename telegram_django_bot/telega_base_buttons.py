from telegram import (
    InlineKeyboardButton as inlinebutt,
)


class ButtonPagination:
    """
    buttons -- массив кнопок с значением, которые отображать, формат кнопок:
        [text; value]
    selected_buttons -- выбранные кнопки в таком же формате
    header_buttons -- кнопки, которые закреплены сверху на каждой странице и могут вести в другое местое, формат:
       [text; value; callback_prefix]  -- callback_prefix=None тогда береться self.callback_prefix
    footer_buttons -- аналогично header_buttons
    
    """

    def __init__(
            self,
            callback_prefix,
            buttons=None,
            selected_values=None,
            header_buttons=None,
            footer_buttons=None,
            callback_prefix_context_values=None,
            rows=8,
            columns=1,
    ):
        self.SELECTED_TICK = '✅ '
        self.PREV_PAGE_STR = '<'
        self.NEXT_PAGE_STR = '>'
        self.PAGE_CALLBACK_SYMBOL = 'telega_p'

        self.callback_prefix = callback_prefix
        self.buttons = buttons
        self.header_buttons = header_buttons or []
        self.footer_buttons = footer_buttons or []
        self.callback_prefix_context_values = callback_prefix_context_values
        self.selected_values = selected_values
        self.rows = rows
        self.columns = columns

    @property
    def buttons_per_page(self):
        return self.rows * self.columns

    @property
    def full_callback_prefix(self):
        context_callback = ''
        if self.callback_prefix_context_values:
            context_callback = '-'.join(map(str, self.callback_prefix_context_values)) + '-'
        return self.callback_prefix + context_callback

    def update_values(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self


    def validate(self, button_callback, set_callback_prefix_context_values=True):
        """
        проверка если страница, то правильный формат у нее
        :return:
        """

        button_value = None
        page_num = None

        str_button_value = button_callback.replace(self.callback_prefix, '').split('-')
        callback_prefix_context_values = str_button_value[:-1]

        if self.PAGE_CALLBACK_SYMBOL in str_button_value[-1]:
            page_num = str_button_value[-1].replace(self.PAGE_CALLBACK_SYMBOL, '')
            if page_num.isalnum():
                page_num = int(page_num)
            else:
                raise ValueError(f'page number {page_num}')
        else:
            button_value = str_button_value[-1]

        if set_callback_prefix_context_values:
            self.callback_prefix_context_values = callback_prefix_context_values
        return callback_prefix_context_values, button_value, page_num

    '''
    def get_value_or_show_page(self, button_callback):
        """

        :return:
        """
        
        is_other_page = False
        res_val = None

        callback_prefix_context_values, button_value, page_num = self.validate(button_callback)
        self.callback_prefix_context_values = callback_prefix_context_values
        
        if page_num:
            is_other_page = True
            res_val = self.construct_inline_curr_page(page_num)
        else:
            res_val = button_value
        return is_other_page, res_val
    '''


    def value_page(self, value):
        """
        выбирает какую страницу отобразить по дефолту
        :param value:  значени кнопки
        :return:
        """

        selected_item_index = list(
            map(lambda x: x[1], self.buttons)
        ).index(value)
        return selected_item_index // self.buttons_per_page

    def _select_page_buttons(self, page_num):
        """
        выбирает какие кнопки с значениями выбрать
        :param page_num: Если None, то вызывает _select_page
        :return:
        """
        return self.buttons[page_num * self.buttons_per_page: (page_num + 1) * self.buttons_per_page]

    def construct_inline_curr_page(self, page_num=None,):
        """
        Cтроит inline кнопки (в переписке, не в меню) в формате телеграмм
        :param page_num:
        :return:
        """

        telega_buttons = []
        if page_num is None:
            if self.selected_values:
                page_num = self.value_page(self.selected_values[0])
            else:
                page_num = 0

        value_buttons = self._select_page_buttons(page_num)
        
        for button in self.header_buttons:
            button_callback_data = button[2] or self.full_callback_prefix
            telega_buttons.append(
                [inlinebutt(button[0], callback_data=button_callback_data + button[1])]
            )

        col_index = 0
        for button in value_buttons:
            button_text = ''
            if self.selected_values and (button[1] in self.selected_values):
                button_text += self.SELECTED_TICK

            button_text += button[0]
            button_telegram = inlinebutt(button_text, callback_data=self.full_callback_prefix + button[1])

            if col_index == 0:
                # new row
                telega_buttons.append([button_telegram])
            else:
                # add in last row
                telega_buttons[-1].append(button_telegram)

            col_index += 1
            if col_index == self.columns:
                col_index = 0

        # neighbor pages
        neighbor_buttons = []
        if page_num > 0:
            callback_data = self.full_callback_prefix + self.PAGE_CALLBACK_SYMBOL + str(page_num - 1)
            neighbor_buttons.append(
                inlinebutt(self.PREV_PAGE_STR, callback_data=callback_data)
            )
        if page_num < int(len(self.buttons) / self.buttons_per_page + 0.9999) - 1:
            callback_data = self.full_callback_prefix + self.PAGE_CALLBACK_SYMBOL + str(page_num + 1)
            neighbor_buttons.append(
                inlinebutt(self.NEXT_PAGE_STR, callback_data=callback_data)
            )
        if neighbor_buttons:
            telega_buttons.append(neighbor_buttons)

        for button in self.footer_buttons:
            button_callback_data = button[2] or self.full_callback_prefix
            telega_buttons.append(
                [inlinebutt(button[0], callback_data=button_callback_data + button[1])]
            )

        return telega_buttons


