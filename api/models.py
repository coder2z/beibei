from django.db import models


# Create your models here.

class User(models.Model):  # 用户模型
    username = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=100)
    creat_time = models.DateField('创建时间', auto_now_add=True)
    s_time = models.PositiveIntegerField(default=0)
    num = models.PositiveIntegerField(default=30)


class Word(models.Model):  # 单词模型
    user_id = models.ForeignKey('User', on_delete=models.CASCADE)
    word = models.CharField(max_length=50)
    time = models.PositiveIntegerField(default=0)
    grade = models.PositiveIntegerField(default=0)
    creat_time = models.DateField('创建时间', auto_now_add=True)


class Error(models.Model):  # 错误模型
    user_id = models.ForeignKey('User', on_delete=models.CASCADE)
    word_id = models.ForeignKey('Word', on_delete=models.CASCADE)
