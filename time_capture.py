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

'''Calculates the work time from a given start time and breaks.

Needs to be called cyclical to be able to update the end time of the work.

The times of breaks and targets can be configured in the json file
that is created on the first run.

Writes a log entry for each day into a csv file for each month
(this can be disabled in the json file).'''

import argparse
import datetime
import json
import os


def update(path, now):
    '''Updates the stash file and output with the current time'''

    # load stash file
    stash, stash_file_path = _get_stash(path, now)

    # date changed?
    if now.date() != stash['work']['start'].date():
        if stash['log']:
            _write_log(path, stash)

        stash['work']['start'] = now

    stash['work']['end'] = now

    # write stash to file
    stash_file = open(stash_file_path, 'w')
    json.dump(stash, stash_file, default=_datetime_to_string, indent=2)
    stash_file.close()

    # calculate presence
    presence = get_presence(stash['work'], stash['breaks'])
    presence_str = get_hour_minute_str(presence)
    print('Anwesenheit: {0: >5s} h'.format(presence_str))

    print_target_times(stash)


def _get_stash(path, now):
    '''load the stash file'''
    try:
        stash_file_path = os.path.join(path, 'timeStash.json')
        with open(stash_file_path, 'r') as stash_file:
            stash = json.load(
                stash_file, object_pairs_hook=_string_to_datetime)

    except IOError:
        stash = _init_stash(now)

    return (stash, stash_file_path)


def _init_stash(now):
    '''initialize stash file'''
    work = dict()
    work['start'] = now
    work['end'] = now

    stash = dict()
    stash['log'] = True
    stash['work'] = work
    stash['breaks'] = [{'start': datetime.time(9),
                        'end': datetime.time(9, 15)},
                       {'start': datetime.time(12, 30),
                        'end': datetime.time(13)}]
    stash['targets'] = [480, 600]

    return stash


def _datetime_to_string(obj):
    '''converts datetime.datetime and datetime.time objects to strings'''
    if isinstance(obj, datetime.datetime):
        value = obj.strftime('%Y-%m-%dT%H:%M')
    elif isinstance(obj, datetime.time):
        value = obj.strftime('%H:%M')
    else:
        raise TypeError

    return value


def _string_to_datetime(obj_list):
    '''converts datetime.datetime and datetime.time strings
     in given key value list to datetime objects'''
    new_dict = dict()
    for key, value in obj_list:
        new_value = value
        if isinstance(value, str):
            try:
                new_value = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M')
            except ValueError:
                try:
                    new_value = datetime.time.fromisoformat(value)
                except ValueError:
                    # if value is not a timestring do nothing
                    pass

        new_dict[key] = new_value

    return new_dict


def _write_log(path, stash):
    '''writes a new log entry to the logfile'''

    # calculate attendance of last day
    presence = get_presence(stash['work'], stash['breaks'])
    presence_str = get_hour_minute_str(presence)

    file_name = stash['work']['start'].strftime('%Y_%m.csv')
    with open(os.path.join(path, file_name), 'a') as log_file:
        log_file.write(stash['work']['start'].strftime('%d.%m.%Y;%H:%M;')
                       + stash['work']['end'].strftime('%H:%M;')
                       + presence_str
                       + '\n')


def calc_time_overlap(first, second):
    '''calculates the overlap between two timespans
    first needs to be of type datetime
    second may be of type datetime or time'''

    second = _set_dict_to_date(first['start'].date(), second)

    overlap_start = max(first['start'], second['start'])
    overlap_end = min(first['end'], second['end'])

    overlap = datetime.timedelta()

    if overlap_end > overlap_start:
        overlap = overlap_end - overlap_start

    return overlap


def get_breaks_duration(work, breaks):
    '''calculates the overall duration of the given breaks during the given
    worktime'''

    breaks_duration = datetime.timedelta()

    for single_break in breaks:
        breaks_duration += calc_time_overlap(work, single_break)

    return breaks_duration


def get_presence(work, breaks):
    '''calculates the presence for given work and break times'''

    return work['end'] - work['start'] - get_breaks_duration(work, breaks)


def get_hour_minute_str(timedelta):
    '''returns a string of format HH:MM from the given timedelta'''

    presence_str = str(timedelta)
    return presence_str[:presence_str.rindex(':')]


def _set_dict_to_date(date, duration):
    '''converts time durations into datetime durations'''

    new_duration = dict()
    for key, value in duration.items():
        if isinstance(value, datetime.time):
            new_duration[key] = datetime.datetime.combine(date, value)
        else:
            new_duration[key] = value

    return new_duration


def print_target_times(stash):
    '''prints the target times'''

    for target in stash['targets']:
        target = datetime.timedelta(minutes=target)
        target_time = get_target_time(stash, target)

        target_time_str = target_time.strftime('%H:%M')
        target_str = str(target)[:-3]  # seconds are ignored
        print('{: >5s} h{: >11}'.format(target_str, target_time_str))


def get_target_time(stash, target):
    '''calculates the time when the target work time is reached'''

    work = dict()
    work['start'] = stash['work']['start']
    work['end'] = work['start'] + target

    while True:

        presence = get_presence(work, stash['breaks'])
        missing_time = target - presence

        if missing_time > datetime.timedelta():
            work['end'] += missing_time
        else:
            break

    return work['end']


def main():
    '''main entry point'''

    formatter = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument('--path', '-p',
                        help='path to folder where logs and stash are stored',
                        dest='path', default=os.path.dirname(os.path.realpath(__file__)))
    args = parser.parse_args()

    now = datetime.datetime.now()

    update(args.path, now)


if __name__ == '__main__':

    main()
