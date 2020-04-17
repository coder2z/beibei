import json
import string
from functools import reduce

from django.db.models import Q
from django.contrib.auth.hashers import make_password, check_password
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from django.db import transaction
from django.http import HttpResponse
from PIL import Image
from django.db.models.query import QuerySet
import pytesseract
from django.views import View
from rest_framework_jwt.authentication import jwt_decode_handler
from rest_framework_jwt.settings import api_settings
from api import models
from api.models import Word, Error, User


def rep(msg, data, code):
    return {"code": code, "data": data, "msg": msg}


def getUser(request):
    token = request.META.get('HTTP_TOKEN')
    toke_user = jwt_decode_handler(token)
    return toke_user


def img(request):
    if request.method == 'POST':
        fe = request.FILES.get('img', None)
        if fe is not None:
            text = pytesseract.image_to_string(Image.open(fe))
            for c in string.punctuation:
                text = text.replace(c, '')
            result = rep("解析成功", text.replace("\n", ""), 200)
        else:
            result = rep("请上传图片", None, 100)
    else:
        result = rep("非法请求", data=None, code=100)
    return HttpResponse(json.dumps(result, ensure_ascii=False), content_type="application/json,charset=utf-8")


def login(request):
    if request.method == 'POST':
        user_name = request.POST.get('name', None)
        pass_word = request.POST.get('password', None)
        if user_name and pass_word:
            user_name = user_name.strip()
            try:
                user = models.User.objects.get(username=user_name)
                if check_password(pass_word, user.password):
                    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
                    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
                    payload = jwt_payload_handler(user)
                    token = jwt_encode_handler(payload)
                    data = {
                        "token": token,
                        "name": user.username,
                        "s_time": user.s_time,
                        "token_time": 8,
                    }
                    result = rep("登录成功", data, 200)
                else:
                    result = rep("账号或者密码错误", None, 100)
            except:
                result = rep("账号或者密码错误", None, 100)
        else:
            result = rep("参数错误", None, 100)
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type="application/json,charset=utf-8")
    else:
        return HttpResponse(json.dumps(rep("非法请求", None, 100), ensure_ascii=False),
                            content_type="application/json,charset=utf-8")


def res(request):
    if request.method == 'POST':
        user_name = request.POST.get('name', None)
        pass_word = request.POST.get('password', None)
        c_pass_word = request.POST.get('c_password', None)
        if c_pass_word == pass_word:
            if user_name and pass_word:
                user_name = user_name.strip()
                pass_word = make_password(pass_word)
                try:
                    models.User.objects.get(user=user_name)
                    result = rep("用户名已经注册", None, 100)
                except:
                    try:
                        user = models.User.objects.create(username=user_name, password=pass_word)
                        if user:
                            result = rep("注册成功", None, 200)
                        else:
                            result = rep("注册失败", None, 100)
                    except:
                        result = rep("注册失败", None, 100)
            else:
                result = rep("参数错误", None, 100)
        else:
            result = rep("两次密码不一致", None, 100)
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type="application/json,charset=utf-8")
    else:
        return HttpResponse(json.dumps(rep("非法请求", None, 100), ensure_ascii=False),
                            content_type="application/json,charset=utf-8")


def upload(request):
    if request.method == 'POST':
        text = request.POST.get('text', None)
        if text is not None:
            text_arr = list(set(text.split(" ")))
            userInfo = getUser(request)
            ushering = models.User.objects.get(id=userInfo['user_id'])
            Word_list = Word.objects.filter(user_id=userInfo['user_id'])
            for x in Word_list:
                if x.word in text_arr:
                    text_arr.remove(x.word)
            word_list_to_insert = list()
            try:
                with transaction.atomic():
                    for x in text_arr:
                        word_list_to_insert.append(Word(user_id=ushering, word=x, time=ushering.s_time))
                    Word.objects.bulk_create(word_list_to_insert)
                    result = rep("提交成功", None, 200)
            except:
                result = rep("提交失败", None, 100)
        else:
            result = rep("参数错误", None, 100)
    else:
        result = rep("非法请求", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def ref(request):
    userInfo = models.User.objects.get(id=getUser(request)["user_id"])
    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
    payload = jwt_payload_handler(userInfo)
    token = jwt_encode_handler(payload)
    if token is not None:
        data = {
            "token": token,
        }
        result = rep("刷新成功", data, 200)
    else:
        result = rep("刷新失败", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def study(request):
    if request.method != 'POST':
        data_link = Word.objects.filter(Q(user_id=getUser(request)["user_id"]) &
                                        Q(grade=0)).order_by('?')[:30]
        datas = list()
        for data in data_link:
            item = {}
            item["val"] = data.word
            item["id"] = data.id
            item["iserror"] = False
            item['isreview'] = False
            datas.append(item)
        error_link = Error.objects.filter(user_id=getUser(request)["user_id"])
        for error in error_link:
            item = {}
            item["val"] = error.word_id.word
            item["id"] = error.word_id.id
            item["iserror"] = True
            item['isreview'] = False
            datas.append(item)
        all_link = Word.objects.filter(user_id=getUser(request)["user_id"])
        ushering = models.User.objects.get(id=getUser(request)['user_id'])
        time_s = [1, 3, 7, 15, 0]
        for all in all_link:
            time_c = ushering.s_time - all.time
            if time_c in time_s:
                item = {}
                item["val"] = all.word
                item["id"] = all.id
                item["iserror"] = False
                item['isreview'] = True
                datas.append(item)
        run_function = lambda x, y: x if y in x else x + [y]
        datas = reduce(run_function, [[], ] + datas)
        result = rep("获取成功", datas, 200)
    else:
        result = rep("非法请求", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def word(request, id):
    if request.method != 'POST':
        word = Word.objects.get(id=id)
        if word.grade == 5:
            word.grade = word.grade
        else:
            word.grade = word.grade + 1
        word.save()
        result = rep("标记成功", None, 200)
    else:
        error = Error(word_id=Word.objects.get(id=id), user_id=User.objects.get(id=getUser(request)["user_id"]))
        error.save()
        if error:
            result = rep("记录成功", None, 200)
        else:
            result = rep("记录成功", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def getWord(request):
    if request.method != 'POST':
        data_link = Word.objects.filter(Q(user_id=getUser(request)["user_id"]) &
                                        Q(grade=0) | Q(grade=1)).order_by('?')[:10]
        datas = list()
        for data in data_link:
            item = {}
            item["val"] = data.word
            item["id"] = data.id
            datas.append(item)
        result = rep("获取成功", datas, 200)
    else:
        result = rep("非法请求", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def setting(request):
    if request.method == 'POST':
        num = request.POST.get('num', None)
        if num is not None:
            user = User.objects.get(id=getUser(request)["user_id"])
            user.num = num
            user.save()
            if user:
                result = rep("设置成功", None, 200)
            else:
                result = rep("设置失败", None, 100)
        else:
            result = rep("参数错误", None, 100)
    else:
        user = User.objects.get(id=getUser(request)["user_id"])
        data = {
            "num": user.num
        }
        result = rep("查询成功", data, 200)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def user(request):
    if request.method != 'POST':
        userInfo = getUser(request)
        try:
            not_link = Word.objects.filter(user_id=userInfo['user_id'], grade=0)
            one_link = Word.objects.filter(user_id=userInfo['user_id'], grade=1)
            two_link = Word.objects.filter(user_id=userInfo['user_id'], grade=2)
            three_link = Word.objects.filter(user_id=userInfo['user_id'], grade=3)
            four_link = Word.objects.filter(user_id=userInfo['user_id'], grade=4)
            fives_link = Word.objects.filter(user_id=userInfo['user_id'], grade=5)
            data = {
                "not": len(not_link),
                "one": len(one_link),
                "two": len(two_link),
                "three": len(three_link),
                "four": len(four_link),
                "fives": len(fives_link),
            }
            result = rep("查询成功", data, 200)
        except:
            result = rep("查询失败", None, 100)
    else:
        result = rep("非法请求", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def userStudy(request):
    if request.method != 'POST':
        try:
            user = User.objects.get(id=getUser(request)["user_id"])
            user.s_time = user.s_time + 1
            user.save()
            result = rep("提交成功", None, 200)
        except:
            result = rep("提交失败", None, 100)
    else:
        result = rep("非法请求", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def _django_single_object_to_json(element, ignore=None):
    return dict([(attr, getattr(element, attr)) for attr in [f.name for f in element._meta.fields if f not in ignore]])


def object_to_json(model, ignore=None):
    """
    函数的作用就是将ORM中的Model对象，转化成json对象，再返回给前端
    :param model:
    :param ignore:
    :return:
    """
    if ignore is None:
        ignore = []
    if type(model) in [QuerySet, list]:
        json = []
        for element in model:
            json.append(_django_single_object_to_json(element, ignore))
        return json
    else:
        return _django_single_object_to_json(model, ignore)


def delWord(request, id):
    if request.method != 'POST':
        try:
            word = Word.objects.get(user_id=User.objects.get(id=getUser(request)["user_id"]), id=id).delete()
            if word:
                result = rep("删除成功", None, 200)
            else:
                result = rep("删除失败", None, 100)
        except:
            result = rep("删除失败", None, 100)
    else:
        result = rep("非法请求", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def ok(request):
    if request.method != 'POST':
        try:
            error_link = Error.objects.filter(user_id=getUser(request)["user_id"])
            error_link.delete()
            result = rep("记录成功", None, 200)
        except:
            result = rep("记录失败", None, 100)
    else:
        result = rep("非法请求", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def pw(request):
    if request.method == 'POST':
        y_password = request.POST.get('y_password', None)
        c_password = request.POST.get('c_password', None)
        n_password = request.POST.get('n_password', None)
        if c_password is not None and n_password is not None and y_password is not None:
            if c_password == n_password:
                try:
                    user = models.User.objects.get(id=getUser(request)["user_id"])
                    if check_password(y_password, user.password):
                        user.password = make_password(n_password)
                        user.save()
                        result = rep("修改密码成功", None, 200)
                    else:
                        result = rep("原密码错误", None, 100)
                except:
                    result = rep("修改密码失败", None, 100)
            else:
                result = rep("两次密码不一致", None, 100)
        else:
            result = rep("参数错误", None, 100)
    else:
        result = rep("非法请求", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


class WordView(View):
    def get(self, request):
        try:
            error = ''
            stus = Word.objects.filter(user_id=getUser(request)["user_id"]).order_by('id')
            size = int(request.GET.get('size', '10'))
            page_number = int(request.GET.get('page', '1'))
            paginator = Paginator(stus, size)
            try:
                page = paginator.page(page_number)
            except (EmptyPage, PageNotAnInteger, InvalidPage):
                error = '已经是最后一页了'
                page = paginator.page(paginator.num_pages)
                page_number = paginator.num_pages

            # 3. 开始做分页
            # 假设分页器上只显示5个页码，分页器出现滚动之后，当前页始终在中间，当前页前后各两个页码；
            if paginator.num_pages <= 5:
                # 全部展示，将当前所有页码的值返回给前端
                page_nums = [x for x in range(1, paginator.num_pages + 1)]
            elif page_number < 4:
                # 如果总页数超过5页了，但是当前页的页码小于4的时候，分页器是同样不会滚动的。
                # 1 2 3 4 5
                # 2 3 4 5 6
                # 3 4 5 6 7
                page_nums = [x for x in range(1, 6)]
            elif page_number - 4 >= 0 and page_number <= paginator.num_pages - 2:
                # 如果总页数超过5页了，分页器需要滚动
                page_nums = [x for x in range(page_number - 2, page_number + 3)]
            else:
                # 超过5页，但是已经到最后一页了，页面不再滚动
                page_nums = [x for x in range(paginator.num_pages - 4, paginator.num_pages + 1)]

            # 4. 向前端返回json数据
            previous = page.has_previous()
            next = page.has_next()
            data_list = {}
            i = 0
            for dat in object_to_json(page.object_list):
                del dat['user_id']
                del dat['creat_time']
                data_list[i] = dat
                i = i + 1
            data = {
                "code": 200,
                "message": "获取成功",
                "error": error,
                # 总的数据个数
                "total_pages": len(stus),
                # 是否有上一页
                "has_previous": previous,
                "previous_url": page_number - 1 if previous else None,
                # 是否有下一页
                "has_next": next,
                "next_url": page_number + 1 if next else None,
                "page_nums": page_nums,
                # 当前页的数据列表
                "data": data_list,
                "current_page": page_number,
            }
        except:
            data = rep('获取失败', None, 100)
        return HttpResponse(json.dumps(data, ensure_ascii=False),
                            content_type="application/json,charset=utf-8")
