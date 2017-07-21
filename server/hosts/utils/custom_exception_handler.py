from rest_framework.views import exception_handler

from .constants import CUSTOM_MESSAGES


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # set the custom message if found one
    if response is not None:
        keys_data = response.data.keys()
        for key in keys_data:
            if key in CUSTOM_MESSAGES.keys():
                response.data.update({key: CUSTOM_MESSAGES[key]})
    return response
