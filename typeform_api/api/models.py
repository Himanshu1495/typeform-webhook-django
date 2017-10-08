# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

TYPEFORM_VALUES = [
    ['your question id which maps to the question for name', 'name'], #eg ['123456', 'name'], here 123456 maps to question, "What is your name?"
    ]
# Create your models here.
class Person(models.Model):
    name = models.CharField(max_length=200)
    typeform = models.ForeignKey('TypeformForms', blank=True, null=True)

    def __str__(self):
        return self.name
class TypeformForms(models.Model):
    form_id = models.CharField(max_length=200)
    form_title = models.CharField(max_length=200)
    event_id = models.CharField(max_length=200)
    questions = models.ManyToManyField('TypeformQuestions', blank=True)

    def __str__(self):
        return self.event_id

class TypeformQuestions(models.Model):
    ques_id = models.CharField(max_length=1000)
    ques_title = models.CharField(max_length=1000)
    ques_type = models.CharField(max_length=1000)
    ans_type = models.CharField(max_length=1000)
    answer = models.CharField(max_length=1000)


    def __str__(self):
        return self.ques_title
