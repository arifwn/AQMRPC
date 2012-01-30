
from twisted.python import log
def with_request(f):
    """
    Decorator to cause the request to be passed as the first argument
    to the method. It also log every call.
    """
    
    def _with_request(*args, **kwargs):
        log.msg('Remote Procedure Call to %s()' % f.func_name)
        return f(*args, **kwargs)
    
    _with_request.withRequest = True
    
    return _with_request