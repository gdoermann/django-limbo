import os
from django.core.management.base import NoArgsCommand
from optparse import make_option

def starting_imports():
    from django.db.models.loading import get_models
    for m in get_models():
        exec "from %s import %s" % (m.__module__, m.__name__)
    from datetime import datetime, timedelta
    sdt = datetime.today().date()
    edt = sdt + timedelta(days=1)
    return locals()

def start_plain_shell(use_plain):
    import code
    # Set up a dictionary to serve as the environment for the shell, so
    # that tab completion works on objects that are imported at runtime.
    # See ticket 5082.
    imported_objects = {}
    try: # Try activating rlcompleter, because it's handy.
        import readline
    except ImportError:
        pass
    else:
        # We don't have to wrap the following import in a 'try', because
        # we already know 'readline' was imported successfully.
        import rlcompleter
        readline.set_completer(rlcompleter.Completer(imported_objects).complete)
        readline.parse_and_bind("tab:complete")

    # We want to honor both $PYTHONSTARTUP and .pythonrc.py, so follow system
    # conventions and get $PYTHONSTARTUP first then import user.
    if not use_plain: 
        pythonrc = os.environ.get("PYTHONSTARTUP") 
        if pythonrc and os.path.isfile(pythonrc): 
            try: 
                execfile(pythonrc) 
            except NameError: 
                pass
        # This will import .pythonrc.py as a side-effect
        import user
    code.interact(local=imported_objects)

def start_ipython_shell():
    from IPython.Shell import IPShell
    import IPython
    # Explicitly pass an empty list as arguments, because otherwise IPython
    # would use sys.argv from this script.
    shell = IPython.Shell.IPShell(argv=[])
    shell.mainloop()
    
def start_bpython_shell():
    from bpython import cli
    cli.main(args=[], locals_=starting_imports())
    

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--plain', action='store_true', dest='plain',
            help='Tells Django to use plain Python, not IPython.'),
        make_option('--ipython', action='store_true', dest='ipython',
            help='Tells Django to use ipython.'),
        make_option('--bpython', action='store_true', dest='bpython',
            help='Tells Django to use bpython.'),
    )
    help = "Runs a Python interactive interpreter. Tries to use bPython, if it's available."

    requires_model_validation = False

    def handle_noargs(self, **options):
        # XXX: (Temporary) workaround for ticket #1796: force early loading of all
        # models from installed apps.
        from django.db.models.loading import get_models
        loaded_models = get_models()

        use_plain = options.get('plain', False)
        use_ipython = options.get('ipython', False)
        use_bpython = options.get('bpython', False)

        try:
            if use_plain:
                # Don't bother loading IPython, because the user wants plain Python.
                raise ImportError
            elif use_ipython:
                start_ipython_shell()
            elif use_bpython:
                start_bpython_shell()
            else:
                start_bpython_shell()

        except ImportError:
            # fallback to plain shell if we encounter an ImportError
            start_plain_shell(use_plain)
