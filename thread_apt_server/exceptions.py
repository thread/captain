class BaseHttpException(Exception):
    pass

class Http400(BaseHttpException):
    message = "400 Bad Request"

class Http403(BaseHttpException):
    message = "403 Forbidden"

class Http404(BaseHttpException):
    message = "404 Not Found"

class Http405(BaseHttpException):
    message = "405 Method Not Allowed"
