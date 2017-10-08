# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse
from .models import *
import rest_framework
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
import json
import requests

@api_view(['POST']) #used so that only POST is accepted
@parser_classes((JSONParser,)) #used to parse JSON
def add_new(request):
    event_id = request.data['event_id'] #get event id from the payload
    form_id = request.data['form_response']['form_id'] #get form_id from payload
    form_title = request.data['form_response']['definition']['title']
    ques = request.data['form_response']['definition']['fields'] #get all the details of questions from payload
    ans = request.data['form_response']['answers'] #get all the details of answers from payload
    context_list = [] #create a list
    for q in ques: #iterate through the question details
        temp = {} #create a temporary dictionary
        temp['form_title'] = form_title #add form title to temporary dictionary
        temp['event_id'] = event_id  #add event id to temporary dictionary
        temp['form_id'] = form_id  #add form id to temporary dictionary
        temp['ques_id'] = q['id'] #add question id to temporary dictionary
        temp['ques_title'] = q['title'] #add question title to temporary dictionary
        temp['ques_type'] = q['type'] #add event id to temporary dictionary
        for a in ans:  #iterate through answers to match the id
            if temp['ques_id'] == a['field']['id']: #check if question and answer id matches
                temp['ans_type'] = a['field']['type'] #add answer type to temporary dictionary
                if temp['ans_type'] == 'short_text': #check for the type of answer we receive since each annswer type needs different parsing
                    temp['answer'] = a['text']
                elif temp['ans_type'] == 'multiple_choice': #multiple_choice needs to be handled differently as there is possibility of getting varieties of json response
                    if a['type'] == 'choice': #when type is choice, it will always have either 'label' or 'other'
                        try:
                            temp['answer'] = a['choice']['label']
                        except:
                            temp['answer'] = a['choice']['other']
                    elif a['type'] == 'choices': #when type is choices, we need to create a list to append all the values from json as it may contain only labels or other or both
                        li = []
                        try: #check for 'other'
                            check_other = a['choices']['other']
                            li.append(check_other)
                        except:
                            pass

                        try: #check for labels
                            check_labels = a['choices']['labels']
                            if check_labels != 'null':
                                for z in check_labels:
                                    li.append(z)
                        except:
                            pass
                        temp['answer'] = str(li) #convert list to string
                elif temp['ans_type'] == 'rating':
                    temp['answer'] = str(a['number'])
                elif temp['ans_type'] == 'long_text':
                    temp['answer'] = a['text']
                elif temp['ans_type'] == 'yes_no':
                    temp['answer'] = str(a['boolean'])
                elif temp['ans_type'] == 'email':
                    temp['answer'] = a['email']
                elif temp['ans_type'] == 'number':
                    temp['answer'] = str(a['number'])
                elif temp['ans_type'] == 'date':
                    temp['answer'] = a['date']
        context_list.append(temp) #append the temporary dictionary to context list
    data_to_send = {} #initialise a dictionary
    data_to_send['form_id'] = form_id #fill in form_id
    data_to_send['form_title'] = form_title #fill in form_title
    data_to_send['event_id'] = event_id #fill in event_id
    questions_list = [] #initialise questions_list
    answers_list = [] #initialise answers_list
    for i in context_list: #iterate through context_list, used to get just the questions and answers
        temp_ques = [] #initialise temporary question list
        temp_ques.append(i['ques_title']) #append ques_title to temporary question list
        temp_ques.append(i['ques_type']) #append ques_type to temporary question list
        temp_ques.append(i['ques_id']) #append ques_id to temporary question list
        questions_list.append(temp_ques) #append temporary question list to questions_list
        temp_ans = [] #initialise temporary answer list
        temp_ans.append(i['answer']) #append answer to temporary answer
        temp_ans.append(i['ans_type']) #append ans_type to temporary answer
        answers_list.append(temp_ans) #append temporary answers list to answer_list
    data_to_send['questions'] = questions_list #put questions_list in the data_to_send dictionary
    data_to_send['answers'] = answers_list #put answers_list in the data_to_send dictionary
    for val in TYPEFORM_VALUES: #this step is required to get the name by matching their ids with the ids stored in TYPEFORM_VALUES list in api.models
        counter = 0
        for ques in questions_list:
            if val[0] == ques[2]: #val[0] is used since we have stored the list as ['id','name'] so val[0] will be 'id'
                get_value = val[1]
                if get_value == 'name':
                    user_name = answers_list[counter][0]
            counter += 1
    try:
        check_existance = Person.objects.get(name=user_name) #check if person is already present
    except:
        check_existance = None
    if check_existance == None: #if person is not present then we need to create it and store it in api Model
        new_form = TypeformForms.objects.create(form_id=data_to_send['form_id'],
                                                 form_title=data_to_send['form_title'],
                                                 event_id=data_to_send['event_id'])
        new_form.save()
        counter = 0
        for ques in data_to_send['questions']:
            a = TypeformQuestions.objects.create(ques_id=ques[2],
                                              ques_title=ques[0],
                                              ques_type=ques[1],
                                              ans_type=answers_list[counter][1],
                                              answer=answers_list[counter][0])
            a.save() #save the question details TypeformQuestions
            new_form.questions.add(a) #add question details to ManyToManyField in TypeformForms
            counter += 1
        new_form.save() #save the form
        x = Person.objects.create(name=user_name, typeform=new_form)
        x.save() #save the person
        return Response(status=status.HTTP_200_OK) #return the response status
    else: #if person is present we need to store the answers of questions and just update the typeform foreignkey in api Model
        try:
            check_form = check_existance.typeform #check if the person has a typeform
        except:
            check_form = None
        if check_form == None or check_form == '': #if there is no typeform then we need to create a form, add questions to the form and link the form to the person
            new_form = TypeformForms.objects.create(form_id=data_to_send['form_id'],
                                                     form_title=data_to_send['form_title'],
                                                     event_id=data_to_send['event_id'])
            new_form.save()
            check_existance.typeform = new_form
            check_existance.save() #save the form first and then add questions to it
            counter = 0
            for ques in data_to_send['questions']:
                a = TypeformQuestions.objects.create(ques_id=ques[2],
                                                  ques_title=ques[0],
                                                  ques_type=ques[1],
                                                  ans_type=answers_list[counter][1],
                                                  answer=answers_list[counter][0])
                a.save()
                check_existance.typeform.questions.add(a)
                counter += 1
            check_existance.save()
            return Response(status=status.HTTP_200_OK) #return the response status
        else: #if typeform is already present, it indicates that the person has filled the form more than once. In this case we just need to update its typeform foreignkey
            check_existance.typeform.questions.all().delete() #delete the questions that were previously presnt so that redundancy is avoided
            counter = 0
            for ques in data_to_send['questions']:
                a = TypeformQuestions.objects.create(ques_id=ques[2],
                                                  ques_title=ques[0],
                                                  ques_type=ques[1],
                                                  ans_type=answers_list[counter][1],
                                                  answer=answers_list[counter][0])
                a.save()
                check_existance.typeform.questions.add(a)
                counter += 1
            check_existance.save()
            return Response(status=status.HTTP_200_OK) #return the response status
