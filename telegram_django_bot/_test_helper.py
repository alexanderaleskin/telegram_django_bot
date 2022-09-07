from .models import User, Payment, Goal, TimeModel, Report
from django.utils import timezone
from uuid import uuid4


class TelegramMixin:

    # @classmethod
    def setUpTestData(cls):
        dttm_now = timezone.now()

        cls.tm030 = TimeModel.objects.create(time=TimeModel.BASE_DATETIME + timezone.timedelta(hours=0, minutes=30))
        cls.tm7 = TimeModel.objects.create(time=TimeModel.BASE_DATETIME + timezone.timedelta(hours=7))
        cls.tm730 = TimeModel.objects.create(time=TimeModel.BASE_DATETIME + timezone.timedelta(hours=7, minutes=30))
        cls.tm8 = TimeModel.objects.create(time=TimeModel.BASE_DATETIME + timezone.timedelta(hours=8))
        cls.tm9 = TimeModel.objects.create(time=TimeModel.BASE_DATETIME + timezone.timedelta(hours=9))
        cls.tm20 = TimeModel.objects.create(time=TimeModel.BASE_DATETIME + timezone.timedelta(hours=20))
        cls.tm23 = TimeModel.objects.create(time=TimeModel.BASE_DATETIME + timezone.timedelta(hours=23))

        cls.user1 = User.objects.create_user(
            1096400,
            '',
            '',
            last_name='Васнецов',
            first_name='Иван',
        )

        cls.user2 = User.objects.create_user(
            1,
            '',
            '',
            last_name='Иванов',
            first_name='Иван',
        )

        cls.user3 = User.objects.create_user(
            2,
            '',
            '',
            last_name='Петров',
            first_name='Иван',
        )

        cls.user1_payment1 = Payment.objects.create(
            user=cls.user1,
            dt_from=dttm_now - timezone.timedelta(days=7),
            dt_to=dttm_now + timezone.timedelta(days=21),

            paid=True,
            payment=100,
            check_sum=str(uuid4())
        )

        cls.user1_payment2 = Payment.objects.create(
            user=cls.user1,
            dt_from=dttm_now + timezone.timedelta(days=21),
            dt_to=dttm_now + timezone.timedelta(days=21 + 31),

            paid=True,
            payment=200,
            check_sum=str(uuid4())
        )

        cls.user2_payment1 = Payment.objects.create(
            user=cls.user2,
            dt_from=dttm_now - timezone.timedelta(days=7),
            dt_to=dttm_now + timezone.timedelta(days=21),

            paid=True,
            payment=100,
            check_sum=str(uuid4())
        )

        cls.user3_payment1 = Payment.objects.create(
            user=cls.user3,
            dt_from=dttm_now - timezone.timedelta(days=7),
            dt_to=dttm_now + timezone.timedelta(days=21),

            paid=False,
            payment=100,
            check_sum=str(uuid4())
        )

        cls.user1_goal1 = Goal.objects.create(
            name='user1_goal1',
            status=Goal.STATUS_IN_PROGRESS,
            frequency_day=Goal.FREQ_DAY_D1,
            target_dttm=None,
            measurement=Goal.MEASURE_KM,
            target_value=5,
            completed=True,

            # напоминания
            no_alarms=True,
            user=cls.user1
        )

        cls.user1_goal2 = Goal.objects.create(
            name='user1_goal2',
            status=Goal.STATUS_IN_PROGRESS,
            frequency_day=Goal.FREQ_DAY_D2,
            target_dttm=None,
            measurement=Goal.MEASURE_KM,
            target_value=5,
            completed=True,

            # напоминания
            no_alarms=False,
            user=cls.user1
        )
        cls.user1_goal2.day_alarms.add(cls.tm7, cls.tm20)

        cls.user1_goal3 = Goal.objects.create(
            name='user1_goal3',
            status=Goal.STATUS_IN_PROGRESS,
            frequency_day=Goal.FREQ_DAY_NO,
            target_dttm=dttm_now + timezone.timedelta(days=62),
            measurement=Goal.MEASURE_NO,
            target_value=None,
            completed=True,

            # напоминания
            no_alarms=False,
            user=cls.user1
        )

        cls.user1_goal3.day_alarms.add(cls.tm7)

        cls.user1_goal4 = Goal.objects.create(
            name='user1_goal4',
            status=Goal.STATUS_IN_PROGRESS,
            frequency_day=Goal.FREQ_DAY_1M,
            target_dttm=None,
            measurement=Goal.MEASURE_NO,
            target_value=None,
            completed=True,

            # напоминания
            no_alarms=False,
            user=cls.user1
        )
        cls.user1_goal4.day_alarms.add(cls.tm7)
        cls.user1_goal4_report1 = Report.objects.create(
            dt=dttm_now.replace(day=1).date(),
            goal=cls.user1_goal4,
            dttm_added_value=dttm_now,
            target_value=3,
        )

        cls.user1_goal5 = Goal.objects.create(
            name='user1_goal5',
            status=Goal.STATUS_IN_PROGRESS,
            frequency_day=Goal.FREQ_DAY_NO,
            target_dttm=dttm_now - timezone.timedelta(days=2),
            measurement=Goal.MEASURE_NO,
            target_value=None,
            completed=True,

            # напоминания
            no_alarms=True,
            user=cls.user1
        )

        cls.user2_goal1 = Goal.objects.create(
            name='user2_goal1',
            status=Goal.STATUS_IN_PROGRESS,
            frequency_day=Goal.FREQ_DAY_2W,
            target_dttm=None,
            measurement=Goal.MEASURE_KM,
            target_value=5,
            completed=True,

            # напоминания
            no_alarms=True,
            user=cls.user2
        )

        cls.user3_goal1 = Goal.objects.create(
            name='user3_goal1',
            status=Goal.STATUS_IN_PROGRESS,
            frequency_day=Goal.FREQ_DAY_2W,
            target_dttm=None,
            measurement=Goal.MEASURE_KM,
            target_value=5,
            completed=True,

            # напоминания
            no_alarms=True,
            user=cls.user3
        )






