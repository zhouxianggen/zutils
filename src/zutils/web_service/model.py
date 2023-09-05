import re
import uuid
import json
import urllib
import hashlib
import logging
from time import monotonic
from enum import IntEnum
from datetime import datetime
from dataclasses import dataclass
from typing import (
    Dict,
    Optional,
    Union,
    Tuple, 
    Callable,
    Any
)


GET = 'GET'
POST = 'POST'
PUT = 'PUT'
DELETE = 'DELETE'


class ErrorCode(IntEnum):
    OK = 0
    ERROR = -1 


@dataclass(frozen=True)
class Error(Exception):
    code: int=ErrorCode.ERROR
    detail: str=''


def json_respond(code: int, error: str='', data=None):
    return {'code': code, 'error': error, 'data': data}


class Request(object):
    NOT_A_DEFAULT = str(uuid.uuid4())
    
    def __init__(
        self,
        method: Optional[str] = None,
        uri: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        path_arguments: Optional[Dict[str, str]] = None, 
        ref: Optional[Any] = None
    ) -> None:
        self.start_time = monotonic()
        self.method = method
        self.uri = uri or ""
        self.headers = headers or {}
        self.body = body or b""
        self.path_arguments = path_arguments or {}
        self.ref = ref
        self.path, sep, self.query = uri.partition("?")
        self.arguments = {k:v[0] for k,v in urllib.parse.parse_qs(
                self.query, keep_blank_values=True).items()}
        if self.body and self.body[0] == 123:
            try:
                self.arguments.update(json.loads(self.body))
            except Exception as e:
                pass
        self.arguments.update(self.path_arguments)

    def took(self):
        return int((monotonic() - self.start_time) * 1000)

    def get_argument(self, key, default=NOT_A_DEFAULT, type=None):
        value = self.arguments.get(key)
        if value == 'undefined' or value is None:
            value = default
        if value == Request.NOT_A_DEFAULT:
            raise Error(ErrorCode.REQUEST_ARGUMENT_ERROR, 
                    f'argument {key} not exist')
        if value is not None and type is not None and not isinstance(value, type):
            try:
                if type == list and not isinstance(value, list):
                    value = json.loads(value)
                elif type == dict and not isinstance(value, dict):
                    value = json.loads(value)
                else:
                    value = type(value)
                assert isinstance(value, type)
            except Exception as e:
                raise Error(ErrorCode.REQUEST_ARGUMENT_ERROR,
                        f'argument {key} not type of {type}')
        return value

    def set_argument(self, key, value):
        self.arguments[key] = value
    
    def get_arg(self, key, default=NOT_A_DEFAULT, type=None):
        return self.get_argument(key, default, type)

    def set_arg(self, key, value):
        self.set_argument(key, value)


class Routes(object):
    def __init__(self, prefix=''):
        self.prefix = prefix.strip('/')
        self.routes = []
        self.plain_paths = {}
        self.pattern_paths = {}
        self.add('HEAD', '_heartbeat', lambda r,c: 'ok', private=False)
        self.add('GET', '_list', self.get_routes, private=True)

    def get_routes(self, request, context):
        lst = [{'methods': r['methods'], 'path': r['path'], 'desc': r['desc']}
                for r in self.routes if not r['private']]
        lst.sort(key=lambda x:x['path'])
        return lst

    def format_path(self, path):
        return path.lower().replace('//', '/').strip('/').strip()

    def add(self, methods: Union[str, list], path: str, handler: Callable, 
            desc: str='', private=False):
        if self.prefix:
            path = f'{self.prefix}/{path}'
        self.routes.append({'methods': methods, 'path': path, 
                'handler': handler, 'desc': desc, 'private': private})
        if isinstance(methods, str):
            methods = [methods]
        methods = [x.lower() for x in methods]
        path = self.format_path(path)
        route_type = 'plain'
        for t in path.split('/'):
            m = re.match(r'(<[\w_-]+>|[\w_-]+)', t)
            assert m is not None
            if t[0] == '<':
                route_type = 'pattern'
        if route_type == 'plain':
            assert path not in self.plain_paths
            self.plain_paths[path] = (methods, handler)
        else:
            assert path not in self.pattern_paths
            self.pattern_paths[path] = (methods, handler)

    def match(self, method: str, path: str) -> Tuple[Callable, Dict]:
        method = method.lower()
        path = self.format_path(path)
        r = self.plain_paths.get(path)
        if r and method in r[0]:
            return (r[1], {})
        for p,t in self.pattern_paths.items():
            methods, handler = t
            if method not in methods:
                continue
            a1 = p.split('/')
            a2 = path.split('/')
            if len(a1) != len(a2):
                continue
            path_args = {}
            for a,b in zip(a1, a2):
                if a and a[0] == '<' and a[-1] == '>':
                    path_args[a[1:-1]] = b
                elif a != b:
                    path_args = None
                    break
            if path_args:
                return(handler, path_args)
        raise Error(ErrorCode.REQUEST_PATH_ERROR, 
                f'path {path} not available')
