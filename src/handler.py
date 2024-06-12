from routes.backend_handler import backend_handler
from routes.preProcess_handler import preProcess_handler
from routes.sqsProcess_handler import sqsProcess_handler

def preProcessHandler(event, context):
    return preProcess_handler(event, context)


def backendHandler(event, context):
    return backend_handler(event, context)


def sqsProcessHandler(event, context):
    return sqsProcess_handler(event, context)