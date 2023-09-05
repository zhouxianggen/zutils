from zutils.web_service import TornadoWebService,Routes

routes = Routes('GET', '/hello', lambda (req, ctx): 'world')
service = TornadoWebService(routes, None)
service.run(8888)

