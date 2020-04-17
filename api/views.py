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


def rep(msg, data, code):  # 规定数据返回格式
    return {"code": code, "data": data, "msg": msg}


def getUser(request):  # 内部函数用于从token中获取用户的信息
    token = request.META.get('HTTP_TOKEN')
    toke_user = jwt_decode_handler(token)
    return toke_user


def img(request):  # 图片上传解析
    if request.method == 'POST':  # 判断请求方式
        fe = request.FILES.get('img', None)  # 获取图片
        if fe is not None:
            text = pytesseract.image_to_string(Image.open(fe))  # 使用pytesseract解析图片
            for c in string.punctuation:
                text = text.replace(c, '')  # 使用string.punctuation处理掉标点符号
            result = rep("解析成功", text.replace("\n", ""), 200)
        else:
            result = rep("请上传图片", None, 100)
    else:
        result = rep("非法请求", data=None, code=100)
    return HttpResponse(json.dumps(result, ensure_ascii=False), content_type="application/json,charset=utf-8")  # 返回数据


def login(request):  # 登录函数
    if request.method == 'POST':
        user_name = request.POST.get('name', None)
        pass_word = request.POST.get('password', None)
        if user_name and pass_word:
            user_name = user_name.strip()  # 处理用户名中的空格
            try:
                user = models.User.objects.get(username=user_name)  # 从模型中获取到登录的信息
                if check_password(pass_word, user.password):  # check_password检测密码
                    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # jwt自定义生成token
                    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
                    payload = jwt_payload_handler(user)
                    token = jwt_encode_handler(payload)
                    # 处理数据格式
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


def res(request):  # 注册函数
    if request.method == 'POST':
        user_name = request.POST.get('name', None)
        pass_word = request.POST.get('password', None)
        c_pass_word = request.POST.get('c_password', None)
        if c_pass_word == pass_word:  # 判断两次密码正确
            if user_name and pass_word:  # 判断参数
                user_name = user_name.strip()  # 判断处理空格
                pass_word = make_password(pass_word)  # make_password 生成加密密码
                try:
                    models.User.objects.get(user=user_name)  # 查询数据库重复用户名
                    result = rep("用户名已经注册", None, 100)
                except:
                    try:
                        user = models.User.objects.create(username=user_name, password=pass_word)  # 用户信息注册写入数据库
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


def upload(request):  # 上传单词
    if request.method == 'POST':
        text = request.POST.get('text', None)
        if text is not None:
            text_arr = list(set(text.split(" ")))  # 上传的文本通过空格分隔成数组
            userInfo = getUser(request)
            ushering = models.User.objects.get(id=userInfo['user_id'])  # 获取当前用户信息
            Word_list = Word.objects.filter(user_id=userInfo['user_id'])  # 获取当前用户的全部单词信息
            for x in Word_list:
                if x.word in text_arr:
                    text_arr.remove(x.word)  # 对单词进行查重
            word_list_to_insert = list()
            try:
                with transaction.atomic():  # 开启数据库事务 这里涉及到批量插入
                    for x in text_arr:
                        word_list_to_insert.append(Word(user_id=ushering, word=x, time=ushering.s_time))  # 生成插入数组
                    Word.objects.bulk_create(word_list_to_insert)  # 批量插入
                    result = rep("提交成功", None, 200)
            except:
                result = rep("提交失败", None, 100)
        else:
            result = rep("参数错误", None, 100)
    else:
        result = rep("非法请求", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def ref(request):  # 刷新token
    userInfo = models.User.objects.get(id=getUser(request)["user_id"])  # 获取到当前用户信息
    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 自定义生成jwt
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


def study(request):  # 生成学习数据
    if request.method != 'POST':
        user = User.objects.get(id=getUser(request)["user_id"])  # 查询用户设置的每日数量
        data_link = Word.objects.filter(Q(user_id=getUser(request)["user_id"]) &
                                        Q(grade=0)).order_by('?')[
                    :user.num]  # 数据库查询当前用户还没有学习的单词 也就是等级为0的单词 随机取user.num个不到user.num个全部去除。
        datas = list()
        for data in data_link:  # 对查询出来的数据进行数据重构
            item = {}
            item["val"] = data.word
            item["id"] = data.id
            item["iserror"] = False
            item['isreview'] = False
            datas.append(item)
        error_link = Error.objects.filter(user_id=getUser(request)["user_id"])  # 查询出当前用户数据库冲标记为错误的单词
        for error in error_link:
            item = {}
            item["val"] = error.word_id.word
            item["id"] = error.word_id.id
            item["iserror"] = True
            item['isreview'] = False
            datas.append(item)
        all_link = Word.objects.filter(user_id=getUser(request)["user_id"])  # 查询出当前用户数据库所有单词
        ushering = models.User.objects.get(id=getUser(request)['user_id'])  # 查询出当前用户的基本信息
        time_s = [1, 3, 7, 15, 0]  # 定义判断时间
        for all in all_link:
            time_c = ushering.s_time - all.time  # 计算出今天距离这个单词第一次学习的时间的差
            if time_c in time_s:  # 判断时间
                item = {}
                item["val"] = all.word
                item["id"] = all.id
                item["iserror"] = False
                item['isreview'] = True
                datas.append(item)
        run_function = lambda x, y: x if y in x else x + [y]  # 对数据进行去重
        datas = reduce(run_function, [[], ] + datas)
        result = rep("获取成功", datas, 200)
    else:
        result = rep("非法请求", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def word(request, id):  # get修改单词的等级 每次加一 最多加到5  post记录错误单词
    if request.method != 'POST':
        word = Word.objects.get(id=id)  # 查询当前单词星级
        if word.grade == 5:  # 判断星级最高
            word.grade = word.grade
        else:
            word.grade = word.grade + 1  # 星级加一
        word.save()
        result = rep("标记成功", None, 200)
    else:
        error = Error(word_id=Word.objects.get(id=id),
                      user_id=User.objects.get(id=getUser(request)["user_id"]))  # 保存错误单词
        error.save()
        if error:
            result = rep("记录成功", None, 200)
        else:
            result = rep("记录成功", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def getWord(request):  # 生成题库
    if request.method != 'POST':
        data_link = Word.objects.filter(Q(user_id=getUser(request)["user_id"]) &
                                        Q(grade=0) | Q(grade=1)).order_by('?')[:10]  # 随机取出今天学习的10各题
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


def setting(request):  # 查询和修改每日目标
    if request.method == 'POST':
        num = request.POST.get('num', None)
        if num is not None:
            user = User.objects.get(id=getUser(request)["user_id"])  # 查询当前的目标
            user.num = num
            user.save()
            if user:
                result = rep("设置成功", None, 200)
            else:
                result = rep("设置失败", None, 100)
        else:
            result = rep("参数错误", None, 100)
    else:
        user = User.objects.get(id=getUser(request)["user_id"])  # 查询当前的目标
        data = {
            "num": user.num
        }
        result = rep("查询成功", data, 200)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def user(request):  # 查询当前用户的各等级数量
    if request.method != 'POST':
        userInfo = getUser(request)
        try:
            not_link = Word.objects.filter(user_id=userInfo['user_id'], grade=0)  # 查询还没学习
            one_link = Word.objects.filter(user_id=userInfo['user_id'], grade=1)  # 查询等级为1
            two_link = Word.objects.filter(user_id=userInfo['user_id'], grade=2)  # 查询等级为2
            three_link = Word.objects.filter(user_id=userInfo['user_id'], grade=3)  # 查询等级为3
            four_link = Word.objects.filter(user_id=userInfo['user_id'], grade=4)  # 查询等级为4
            fives_link = Word.objects.filter(user_id=userInfo['user_id'], grade=5)  # 查询等级为5
            # 获取个数
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


def userStudy(request):  # 学习时间加一
    if request.method != 'POST':
        try:
            user = User.objects.get(id=getUser(request)["user_id"])  # 查询学习时间
            user.s_time = user.s_time + 1  # 学习时间加一
            user.save()
            result = rep("提交成功", None, 200)
        except:
            result = rep("提交失败", None, 100)
    else:
        result = rep("非法请求", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def _django_single_object_to_json(element, ignore=None):  # 工具函数 处理分页数据
    return dict([(attr, getattr(element, attr)) for attr in [f.name for f in element._meta.fields if f not in ignore]])


def object_to_json(model, ignore=None):  # 工具函数 处理分页数据
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


def delWord(request, id):  # 删除单词
    if request.method != 'POST':
        try:
            word = Word.objects.get(user_id=User.objects.get(id=getUser(request)["user_id"]), id=id).delete()  # 删除单词
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


def ok(request):  # 记录每日学习任务完成
    if request.method != 'POST':
        try:
            error_link = Error.objects.filter(user_id=getUser(request)["user_id"])  # 删除错误表
            error_link.delete()
            result = rep("记录成功", None, 200)
        except:
            result = rep("记录失败", None, 100)
    else:
        result = rep("非法请求", None, 100)
    return HttpResponse(json.dumps(result, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")


def pw(request):  # 修改密码
    if request.method == 'POST':
        y_password = request.POST.get('y_password', None)
        c_password = request.POST.get('c_password', None)
        n_password = request.POST.get('n_password', None)
        if c_password is not None and n_password is not None and y_password is not None:
            if c_password == n_password:
                try:
                    user = models.User.objects.get(id=getUser(request)["user_id"])
                    if check_password(y_password, user.password):  # 验证原密码
                        user.password = make_password(n_password)  # 生成加密密码并修改
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


class WordView(View):  # 获取本人全部单词分页
    def get(self, request):  # 定义get请求
        try:
            error = ''
            stus = Word.objects.filter(user_id=getUser(request)["user_id"]).order_by('id')  # 查询所有自己的单词
            size = int(request.GET.get('size', '10'))  # 获取每页数量默认10
            page_number = int(request.GET.get('page', '1'))  # 获取页码默认1
            paginator = Paginator(stus, size)  # 创建分页对象
            try:
                page = paginator.page(page_number)  # 分页
            except (EmptyPage, PageNotAnInteger, InvalidPage):  # 判断是否超过最后一页
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
            # 分页数据进行处理
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
