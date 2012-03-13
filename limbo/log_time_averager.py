"""
This will look for limbo.debug.Ticker outputs and show the name you associated, the avg, max and min times
ordered by avg time.

Usage:
tail -f /var/log/my.log | python /path/to/limbo/log_time_averager.py

"""
import re
import time
import sys
import datetime
import traceback
from django.template.defaultfilters import slugify
from django.utils.datastructures import SortedDict
import curses


class LogTimerAverage(object):
    regex = re.compile('.*} (.*) (\d+):(\d+):(\d+)\.(\d+)')
    format = '%-50s  %-16s %-16s %-16s %-10s'
    header_line = format %("Name", "Avg.", "Max", "Min", "Sample")
    def __init__(self):
        self.messages = SortedDict()
        self.last_print=None
        self.stdscr = curses.initscr()
        self.stdscr.refresh()

    def read_from_stdin(self):
        while True:
            try:
                line = sys.stdin.readline()
            except IOError:
                time.sleep(.1)
                continue
            if line:
                if self.regex.match(line):
                    self.process(line)
            else:
                time.sleep(.01)

    def process(self, line):
        name, hrs, minutes, seconds, milliseconds = self.regex.match(line).groups()
        key = name.strip()
        if key.endswith('-') or key.endswith(':') or key.endswith('.'):
            key = key[:-1].strip()
        delta = datetime.timedelta(hours=int(hrs), minutes=int(minutes), seconds = float('%s.%s' %(seconds, milliseconds)))
        msgs = self.messages.get(key, [])
        msgs.append(delta)
        if len(msgs) > 1000:
            msgs = msgs[:-1000]
        self.messages[key] = msgs
        self.full_print()

    def full_print(self):
        if self.last_print and (datetime.datetime.now() - self.last_print < datetime.timedelta(seconds=3)):
            return
        d = SortedDict()
        for name, deltas in self.messages.items():
            sum = datetime.timedelta()
            for delta in deltas:
                sum += delta
            avg = sum / len(deltas)
            mx = max(deltas)
            mn = min(deltas)
            if len(name) > 50:
                name = name[:50]
            line = self.format %(name, avg, mx, mn, len(deltas))
            d[avg] = line

        d.keyOrder.sort()
        d.keyOrder.reverse()
        line_number = 3
        self.stdscr.clear()

        self.stdscr.addstr(1, 4, self.header_line)

        for line in d.values():
            try:
                self.stdscr.addstr(line_number, 4, line)
            except Exception:
                break
            line_number += 1

        self.stdscr.refresh()
        self.last_print = datetime.datetime.now()

    def stop(self):
        # curses.endwin()
        sys.exit()



if __name__ == '__main__':
    averager = LogTimerAverage()
    try:
        averager.read_from_stdin()
    except KeyboardInterrupt:
        averager.stop()
    except (Exception, RuntimeError):
        averager.stop()
        traceback.print_exc()
