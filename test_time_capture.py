#!/usr/bin/env python3
# Copyright 2019 Michael Köcher

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''unit tests for time_capture.py'''

import unittest
from unittest.mock import patch
import datetime
import time_capture


class TestTimeCaptureGetStash(unittest.TestCase):

    '''unit tests for get_stash'''
    @patch('time_capture.open')
    @patch('time_capture._init_stash')
    def test_stash_file_not_found(self, mockinit, mockopen):
        '''file cannot be opend'''
        mockopen.side_effect = IOError('File not found')

        time_capture._get_stash('./test/', None)

        mockinit.assert_called()

    @patch('time_capture.json.load')
    @patch('time_capture.open')
    def test_stash_json_decode_error(self, _, mockload):
        '''file contents cannot be decoded'''
        mockload.side_effect = time_capture.json.JSONDecodeError(
            'Wrong', 'TimeStash.json', 13)
        with self.assertRaises(time_capture.json.JSONDecodeError):
            time_capture._get_stash('./test/', None)


class TestTimeCaptureInit(unittest.TestCase):

    '''unit tests for init'''

    def test_init_stash(self):
        '''tests if the stash file is correctly created'''

        test_time = time_capture.datetime.datetime(2008, 8, 1, 8)
        stash = time_capture._init_stash(test_time)

        # püfen der Parameter der Funktion pickle.dump
        expected_work = dict()
        expected_work['start'] = test_time
        expected_work['end'] = test_time

        expected_stash = dict()
        expected_stash['log'] = True
        expected_stash['work'] = expected_work
        expected_stash['breaks'] = [{'start': datetime.time(9),
                                     'end': datetime.time(9, 15)},
                                    {'start': datetime.time(12, 30),
                                     'end': datetime.time(13)}]
        expected_stash['targets'] = [480, 600]

        self.assertEqual(stash, expected_stash)


class TestTimeCaptureDatetimeToString(unittest.TestCase):
    '''testcase for _datetime_to_string'''

    def test_convert_datetime_object(self):
        '''convert a datetime object'''
        test_datetime = datetime.datetime(2000, 1, 1, 12, 15)

        expected = '2000-01-01T12:15'

        result = time_capture._datetime_to_string(test_datetime)

        self.assertEqual(result, expected)

    def test_convert_time_object(self):
        '''convert a time object'''
        test_datetime = datetime.time(12, 15)

        expected = '12:15'

        result = time_capture._datetime_to_string(test_datetime)

        self.assertEqual(result, expected)


class TestTimeCaptureStringToDatetime(unittest.TestCase):
    '''testcase for _string_to_datetime'''

    def test_some_strings_to_datetimes(self):
        '''convert a complete dict'''
        test_list = [('one', '2000-01-01T12:15'),
                     ('two', '2001-05-12T15:23'),
                     ('three', 5),
                     ('four', 'hello world'),
                     ('five', '13:36')]
        expected_dict = {'one': datetime.datetime(2000, 1, 1, 12, 15),
                         'two': datetime.datetime(2001, 5, 12, 15, 23),
                         'three': 5,
                         'four': 'hello world',
                         'five': datetime.time(13, 36)}

        result = time_capture._string_to_datetime(test_list)

        self.assertEqual(result, expected_dict)


class TestWriteLog(unittest.TestCase):
    '''unit tests for _write_log'''

    def test_log(self):
        '''creation of a log line'''
        test_work = dict()
        test_work['start'] = datetime.datetime(2000, 2, 4, 7, 30)
        test_work['end'] = datetime.datetime(2000, 2, 4, 17, 45)

        test_stash = dict()
        test_stash['work'] = test_work
        test_stash['breaks'] = [{'start': datetime.time(9),
                                 'end': datetime.time(9, 15)},
                                {'start': datetime.time(12, 30),
                                 'end': datetime.time(13)}]

        mockopen = unittest.mock.mock_open()
        with patch('time_capture.open', mockopen):
            time_capture._write_log('/path/to/file', test_stash)

        mockopen.assert_called_with('/path/to/file/2000_02.csv', 'a')
        mockwrite = mockopen()
        mockwrite.write.assert_called_with('04.02.2000;07:30;17:45;9:30\n')


class TestTimeCaptureCalcTimeOverlap(unittest.TestCase):

    '''unit tests for calc_time_overlap'''

    def test_full_overlap(self):
        '''full overlap'''
        first = {'start': datetime.datetime(2000, 1, 1, 7),
                 'end': datetime.datetime(2000, 1, 1, 9, 30)}
        second = {'start': datetime.datetime(2000, 1, 1, 9),
                  'end': datetime.datetime(2000, 1, 1, 9, 15)}
        break_time = time_capture.calc_time_overlap(first, second)

        self.assertEqual(break_time, datetime.timedelta(minutes=15))

    def test_first_ends_during_second(self):
        '''first ends during second'''
        first = {'start': datetime.datetime(2000, 1, 1, 7),
                 'end': datetime.datetime(2000, 1, 1, 9, 5)}
        second = {'start': datetime.datetime(2000, 1, 1, 9),
                  'end': datetime.datetime(2000, 1, 1, 9, 15)}
        break_time = time_capture.calc_time_overlap(first, second)

        self.assertEqual(break_time, datetime.timedelta(minutes=5))

    def test_first_starts_during_second(self):
        '''first starts during second'''
        first = {'start': datetime.datetime(2000, 1, 1, 9, 10),
                 'end': datetime.datetime(2000, 1, 1, 9, 30)}
        second = {'start': datetime.datetime(2000, 1, 1, 9),
                  'end': datetime.datetime(2000, 1, 1, 9, 15)}
        break_time = time_capture.calc_time_overlap(first, second)

        self.assertEqual(break_time, datetime.timedelta(minutes=5))

    def test_first_starts_and_ends_during_second(self):
        '''first starts and ends during second'''
        first = {'start': datetime.datetime(2000, 1, 1, 9, 5),
                 'end': datetime.datetime(2000, 1, 1, 9, 10)}
        second = {'start': datetime.datetime(2000, 1, 1, 9),
                  'end': datetime.datetime(2000, 1, 1, 9, 15)}
        break_time = time_capture.calc_time_overlap(first, second)

        self.assertEqual(break_time, datetime.timedelta(minutes=5))

    def test_no_overlap(self):
        '''no overlap'''
        first = {'start': datetime.datetime(2000, 1, 1, 7),
                 'end': datetime.datetime(2000, 1, 1, 7, 30)}
        second = {'start': datetime.datetime(2000, 1, 1, 9),
                  'end': datetime.datetime(2000, 1, 1, 9, 15)}
        break_time = time_capture.calc_time_overlap(first, second)

        self.assertEqual(break_time, datetime.timedelta(minutes=0))

    def test_second_is_time(self):
        '''no overlap'''
        first = {'start': datetime.datetime(2000, 1, 1, 9, 5),
                 'end': datetime.datetime(2000, 1, 1, 9, 10)}
        second = {'start': datetime.time(9),
                  'end': datetime.time(9, 15)}
        break_time = time_capture.calc_time_overlap(first, second)

        self.assertEqual(break_time, datetime.timedelta(minutes=5))


class TestTimeCaptureGetBreaksDuration(unittest.TestCase):
    '''unittests for get_breaks_duration'''

    def test_all_breaks_covered(self):
        '''all breaks are covered'''
        breaks = [{'start': datetime.datetime(2000, 1, 1, 9),
                   'end': datetime.datetime(2000, 1, 1, 9, 15)},
                  {'start': datetime.datetime(2000, 1, 1, 12, 30),
                   'end': datetime.datetime(2000, 1, 1, 13)}]
        work = {'start': datetime.datetime(2000, 1, 1, 7),
                'end': datetime.datetime(2000, 1, 1, 17)}

        breaks_time = time_capture.get_breaks_duration(work, breaks)

        self.assertEqual(breaks_time, datetime.timedelta(minutes=45))

    def test_no_break_covered(self):
        '''no break is covered'''
        breaks = [{'start': datetime.datetime(2000, 1, 1, 9),
                   'end': datetime.datetime(2000, 1, 1, 9, 15)},
                  {'start': datetime.datetime(2000, 1, 1, 12, 30),
                   'end': datetime.datetime(2000, 1, 1, 13)}]
        work = {'start': datetime.datetime(2000, 1, 1, 9, 30),
                'end': datetime.datetime(2000, 1, 1, 12)}

        breaks_time = time_capture.get_breaks_duration(work, breaks)

        self.assertEqual(breaks_time, datetime.timedelta(minutes=0))

    def test_no_breaks_given(self):
        '''no breaks are given'''
        breaks = []
        work = {'start': datetime.datetime(2000, 1, 1, 9, 30),
                'end': datetime.datetime(2000, 1, 1, 12)}

        breaks_time = time_capture.get_breaks_duration(work, breaks)

        self.assertEqual(breaks_time, datetime.timedelta(minutes=0))


class TestTimeCaptureGetPresence(unittest.TestCase):
    '''untitests for get_presence'''

    def test_presence_of_full_work_day(self):
        '''presence of a full work day'''
        breaks = [{'start': datetime.datetime(2000, 1, 1, 9),
                   'end': datetime.datetime(2000, 1, 1, 9, 15)},
                  {'start': datetime.datetime(2000, 1, 1, 12, 30),
                   'end': datetime.datetime(2000, 1, 1, 13)}]
        work = {'start': datetime.datetime(2000, 1, 1, 7),
                'end': datetime.datetime(2000, 1, 1, 17)}

        presence = time_capture.get_presence(work, breaks)

        self.assertEqual(presence, datetime.timedelta(hours=9, minutes=15))


class TestTimeCaptureGetTargetTime(unittest.TestCase):
    '''unittests for get_target_time'''

    def test_target_covers_multiple_breaks(self):
        '''multiple runs of the loop are necessary'''

        breaks = [{'start': datetime.datetime(2000, 1, 1, 9),
                   'end': datetime.datetime(2000, 1, 1, 9, 15)},
                  {'start': datetime.datetime(2000, 1, 1, 10, 5),
                   'end': datetime.datetime(2000, 1, 1, 10, 10)}]
        work = {'start': datetime.datetime(2000, 1, 1, 7)}
        stash = {'breaks': breaks, 'work': work}

        target = datetime.timedelta(minutes=180)

        target_time = time_capture.get_target_time(stash, target)

        self.assertEqual(target_time, datetime.datetime(2000, 1, 1, 10, 20))


if __name__ == '__main__':
    unittest.main()
