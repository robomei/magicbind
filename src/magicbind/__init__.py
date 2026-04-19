def load_ipython_extension(ip):
    from magicbind.magic import load_ipython_extension as _load
    _load(ip)
