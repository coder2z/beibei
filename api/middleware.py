# 创建app/middleware.py并编辑
import json
import time

from rest_framework_jwt.views import refresh_jwt_token
from django.http import JsonResponse, HttpResponse
from rest_framework_jwt.authentication import jwt_decode_handler


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.ref = False

    def __call__(self, request):
        response = self.get_response(request)
        if self.ref:
            response.status_code = 210
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path_info != "/api/user/login/" and request.path_info != "/api/user/res/":
            token = request.META.get('HTTP_TOKEN')
            if token is None:
                return HttpResponse(json.dumps({"code": 403, "data": None, "msg": "token未知"}, ensure_ascii=False),
                                    content_type="application/json,charset=utf-8", status=403)
            else:
                toke_user = jwt_decode_handler(token)
                if int(time.time()) > toke_user['exp'] + 24 * 60 * 60 * 1000:
                    return HttpResponse(json.dumps({"code": 403, "data": None, "msg": "token过期"}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8", status=403)
                elif int(time.time()) > toke_user['exp']:
                    self.ref = True
