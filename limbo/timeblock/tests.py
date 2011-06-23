import datetime
from limbo.testing import BaseTestCase
from limbo.timeblock import calcs
from limbo.timeblock.logic import TimeBlock, TimeChoices

class Logic(BaseTestCase):
    def test_timeblock(self):
        today = datetime.datetime.now().date()

        seven = datetime.datetime.combine(today, datetime.time(7,00))
        eight = datetime.datetime.combine(today, datetime.time(8,00))
        nine = datetime.datetime.combine(today, datetime.time(9,00))
        ten = datetime.datetime.combine(today, datetime.time(10,00))
        eleven = datetime.datetime.combine(today, datetime.time(11,00))
        nine_fifty = datetime.datetime.combine(today, datetime.time(9,50))
        ten_o_five = datetime.datetime.combine(today, datetime.time(10,05))

        seven_to_eight = TimeBlock(seven, eight)
        seven_to_ten = TimeBlock(seven, ten)
        seven_to_eleven = TimeBlock(seven, eleven)
        nine_to_ten = TimeBlock(nine, ten)
        ten_to_eleven = TimeBlock(ten, eleven)

        # Test overlaps
        self.assertTrue(seven_to_ten.overlaps(nine_to_ten))
        self.assertTrue(nine_to_ten.overlaps(seven_to_ten))
        self.assertTrue(seven_to_ten.overlaps(ten_to_eleven))

        # Test before
        self.assertTrue(seven_to_eight.before(ten_to_eleven))
        self.assertFalse(ten_to_eleven.before(seven_to_eight))
        self.assertTrue(seven_to_eight.before(nine_to_ten))

        # Test After
        self.assertTrue(ten_to_eleven.after(seven_to_eight))
        self.assertFalse(seven_to_eight.after(ten_to_eleven))

        # Test fully_overlaps
        self.assertTrue(seven_to_ten.fully_overlaps(nine_to_ten))
        self.assertTrue(seven_to_ten.overlaps(nine_to_ten))
        self.assertFalse(seven_to_ten.fully_overlaps(seven_to_eleven))
        self.assertTrue(seven_to_eleven.fully_overlaps(seven_to_eight))

        # Test Less Than
        self.assertFalse(seven_to_eight <= seven_to_eleven)
        self.assertTrue(seven_to_ten <= ten_to_eleven)
        self.assertFalse(seven_to_ten < ten_to_eleven)
        self.assertTrue(seven_to_eight < ten_to_eleven)

        # Test Greater Than
        self.assertTrue(ten_to_eleven >= seven_to_ten)
        self.assertFalse(seven_to_ten >= ten_to_eleven)
        self.assertTrue(ten_to_eleven > seven_to_eight)
        self.assertFalse(ten_to_eleven > seven_to_ten)

        # Test Add
        self.assertTrue(seven_to_ten + nine_to_ten == seven_to_ten)
        self.assertTrue(seven_to_ten + ten_to_eleven == seven_to_eleven)
        self.assertTrue(nine_to_ten + ten_to_eleven == TimeBlock(nine, eleven))
        self.assertRaises(ValueError, seven_to_eight.__add__, ten_to_eleven)

        # Test Subtract
        try:
            ten_to_eleven - seven_to_ten
            self.fail("You shouldn't be able to subtract values before the given time")
        except ValueError:
            pass
        self.assertRaises(ValueError, ten_to_eleven.__sub__, seven_to_eight)
        self.assertEqual(seven_to_ten - ten_to_eleven, seven_to_ten)
        self.assertEqual(nine_to_ten - seven_to_ten, None)
        self.assertEqual(seven_to_eight - seven_to_ten, None)
        self.assertEqual(seven_to_eight, seven_to_ten - TimeBlock(eight, ten))
        self.assertEqual(nine_to_ten, TimeBlock(nine, eleven) - ten_to_eleven)
        self.assertEqual(ten_to_eleven, TimeBlock(nine, eleven) - seven_to_ten)
        # Partial overlaps
        self.assertEqual(TimeBlock(ten_o_five, eleven), ten_to_eleven - TimeBlock(nine_fifty, ten_o_five))
        self.assertEqual(TimeBlock(nine, nine_fifty), nine_to_ten - TimeBlock(nine_fifty, ten_o_five))

        # Test Split
        self.assertEqual(seven_to_ten.split(TimeBlock(eight, nine)), (seven_to_eight, nine_to_ten))
        self.assertEqual(len(seven_to_ten.split(nine_to_ten)), 1)
        self.assertEqual(len(seven_to_ten.split(seven_to_eight)), 1)
        self.assertEqual(len(seven_to_ten.split(TimeBlock(seven, ten))), 0)

    def test_time_choices(self):
        date = datetime.datetime.now().date()
        five_to = datetime.datetime.combine(date, datetime.time(12,55))
        ten_to = datetime.datetime.combine(date, datetime.time(12,50))
        sixty_min = datetime.timedelta(minutes=60)

        options = TimeChoices()
        self.assertEqual(options.round(five_to), datetime.datetime.combine(date, datetime.time(13,00)))
        self.assertEqual(options.round(ten_to), datetime.datetime.combine(date, datetime.time(12,45)))
        start = five_to
        end = start + sixty_min
        tb = TimeBlock(start, end)
        options.append(tb)
        self.assertEqual(len(options[date]), 3)

        start = options.round(five_to)
        end = start + sixty_min
        tb = TimeBlock(start, end)
        options.append(tb)
        self.assertEqual(len(options[date]), 4)
        self.assertEqual(len(TimeChoices([tb])[date]), 4)
        options.remove(tb)
        self.assertEqual(len(options[date]), 0)

    def test_get_start_end(self):
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=1)

        new_start, new_end = calcs.get_start_end(start, end)
        self.assertEqual(start, new_start)
        self.assertEqual(end, new_end)
        self.assertTrue(new_start < new_end)

        new_start, new_end = calcs.get_start_end(start, end.date())
        self.assertTrue(new_start < new_end)
        self.assertEqual(start.date(), new_start)
        self.assertEqual(end.date(), new_end)

        new_start, new_end = calcs.get_start_end(start.date(), end)
        self.assertTrue(new_start < new_end)
        self.assertEqual(start.date(), new_start)
        self.assertEqual(end.date(), new_end)

    def test_check_datetime_date(self):
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=1)

        new_start, new_end = calcs.check_datetime_date(start, end)
        self.assertEqual(start, new_start)
        self.assertEqual(end, new_end)
        self.assertTrue(new_start < new_end)

        new_start, new_end = calcs.check_datetime_date(start, end.date())
        self.assertEqual(type(new_start), type(new_end))
        self.assertEqual(start.date(), new_start)
        self.assertEqual(end.date(), new_end)
        self.assertTrue(new_start < new_end)
