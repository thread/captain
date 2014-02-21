class HttpException(Exception):
    pass

class Http400(HttpException):
    message = "400 Bad Request"

class Http403(HttpException):
    message = "403 Forbidden"

class Http404(HttpException):
    message = "404 Not Found"

class Http405(HttpException):
    message = "405 Method Not Allowed"
