import concurrent
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.web import Application, RequestHandler
from .. import get_logger
from .model import (
        json_respond,
        Request,
        Error, 
        ErrorCode)


class TornadoWebService(Application):
    def __init__(self, routes, context=None, 
            logger=get_logger('TornadoWebService')):
        self.logger = logger
        handlers = [(r"(.+?)", ServiceRequestHandler, 
                {'routes': routes, 'context': context, 'logger': logger})]
        settings = dict(debug=True, )
        Application.__init__(self, handlers, **settings)

    def run(self, port):
        self.listen(port)
        self.logger.info(f'service start on {port} ..')
        IOLoop.instance().start()


class ServiceRequestHandler(RequestHandler):
    executor = concurrent.futures.ThreadPoolExecutor(
            thread_name_prefix='handler')

    def initialize(self, routes, context, logger):
        self.routes = routes
        self.context = context
        self.logger = logger

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    async def head(self, path):
        await self.on_request(path)

    async def post(self, path):
        await self.on_request(path)
    
    async def put(self, path):
        await self.on_request(path)

    async def get(self, path):
        await self.on_request(path)
    
    async def delete(self, path):
        await self.on_request(path)

    async def on_request(self, path):
        if self.request.method != 'HEAD':
            self.logger.info(f'on request {self.request.method}: {path}')
        try:
            resp = await IOLoop.current().run_in_executor(
                    self.executor, self.process_request, path)
            self.finish(json_respond(ErrorCode.OK, '', resp))
        except Error as e:
            self.logger.exception(e)
            self.finish(json_respond(e.code, e.detail))
        except Exception as e:
            self.logger.exception(e)
            self.finish(json_respond(ErrorCode.ERROR, str(e)))

    def process_request(self, path):
        handler, path_args = self.routes.match(self.request.method, path)
        request = Request(method=self.request.method,
            uri=self.request.uri,
            headers=dict(self.request.headers.get_all()),
            body=self.request.body,
            path_arguments=path_args,
            ref=self.request)
        func_name = handler.__name__
        if hasattr(handler, '__self__'):
            func_name = '{}.{}'.format(handler.__self__.__class__.__name__, 
                    func_name)
        try:
            return handler(request, self.context)
        except Exception as e:
            raise
        finally:
            if self.request.method != 'HEAD':
                self.logger.info(f'{func_name} took {request.took()} ms')

