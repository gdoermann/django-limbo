from datetime import datetime, timedelta
from limbo.models import callable_attribute, model_attribute
from limbo.strings import unslugify


class Ticker:
    def __init__(self, name="Ticker", stdout = None, do_print = True):
        self.last_tick = None
        self.splits = None
        self.name = name
        self.stdout = stdout
        self.do_print = do_print

    def start(self):
        if self.last_tick is not None:
            raise ValueError("Timer has already been started.")
        self.last_tick = datetime.now()

    def reset(self):
        self.last_tick = datetime.now()
        self.splits = []

    def __call__(self, *args, **kwargs):
        self.tick(*args, **kwargs)

    def time(self, reset=True):
        if self.last_tick:
            diff = datetime.now() - self.last_tick
        else:
            diff = timedelta()
        if reset:
            self.reset()
        return diff

    def split(self):
        if self.splits is None:
            self.reset()
            return
        self.splits.append(self.time(reset = False))

    def average_split(self, message = "Average Split", reset=True):
        splits = self.splits
        diff = timedelta()
        for s in splits:
            diff += s
        avg = diff/len(splits)
        msg = "%s: %s - %s" %(self.name, message, avg)
        self.log(msg, reset)
        return avg

    def log(self, msg, reset=True):
        if self.do_print:
            if self.stdout:
                self.stdout.write(msg)
            else:
                print msg
        if reset:
            self.reset()

    def tick(self, message, reset=True):
        diff = self.time(reset)
        msg = "%s: %s - %s" %(self.name, message, diff)
        self.log(msg, reset)
        return msg


def print_detail(value, level=0):
    print('\t'*level + value)

def print_details(detail_list, level=0):
    value = '\t'.join([str(d) for d in detail_list])
    print_detail(value, level)

def print_model_detail(model, name, level=0, label=None, label_width=25):
    label = label or unslugify(name.split('__')[-1]).title() + ':'
    value = model_attribute(model, name)
    if callable(value):
        value = callable_attribute(model, value)
    space = label_width - len(label)
    if space > 0:
        label += ' ' * space
    print_details([label, value], level)

