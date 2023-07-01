from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
import pymysql
from django.http import HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import matplotlib.pyplot as plt
import re
import cv2
import numpy as np
from string import punctuation
from nltk.corpus import stopwords
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
import os
from nltk.tokenize import word_tokenize

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()
porter = PorterStemmer()

def LCS(l1,l2): #LCS method
    s1 = word_tokenize(l1)
    s2 = word_tokenize(l2)
    dp = [[None]*(len(s1)+1) for i in range(len(s2)+1)]
    for i in range(len(s2)+1): 
        for j in range(len(s1)+1): 
            if i == 0 or j == 0: 
                dp[i][j] = 0
            elif s2[i-1] == s1[j-1]: 
                dp[i][j] = dp[i-1][j-1]+1
            else: 
                dp[i][j] = max(dp[i-1][j] , dp[i][j-1]) 
    return dp[len(s2)][len(s1)]

def cleanPost(doc):
    tokens = doc.split()
    table = str.maketrans('', '', punctuation)
    tokens = [w.translate(table) for w in tokens]
    tokens = [word for word in tokens if word.isalpha()]
    tokens = [w for w in tokens if not w in stop_words]
    tokens = [word for word in tokens if len(word) > 1]
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    tokens = [porter.stem(token) for token in tokens]
    tokens = ' '.join(tokens)
    return tokens


text_files = []
text_data = []
image_files = []
image_data = []

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})

def Login(request):
    if request.method == 'GET':
       return render(request, 'Login.html', {})

def UploadSuspiciousFile(request):
    if request.method == 'GET':
        return render(request, 'UploadSuspiciousFile.html', {})


def UploadSuspiciousImage(request):
    if request.method == 'GET':
        return render(request, 'UploadSuspiciousImage.html', {})


def UploadSuspiciousImageAction(request):
    if request.method == 'POST' and request.FILES['t1']:
        output = ''
        myfile = request.FILES['t1']
        fs = FileSystemStorage()
        name = str(myfile)
        filename = fs.save(name, myfile)
        img = cv2.imread(name)
        img = cv2.resize(img,(200,200))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([img], [0], None, [256], [0, 256])
        os.remove(name)
        similarity = 0
        file = 'No Match Found'
        hist1 = 0
        for i in range(len(image_files)):
            metric_val = cv2.compareHist(hist, image_data[i], cv2.HISTCMP_INTERSECT)
            if metric_val > similarity:
                similarity = metric_val
                file = image_files[i]
                hist1 = image_data[i]
        output = '<table border=1 align=center><tr><th>Source Original Image Name</th><th>Suspicious Image Name</th><th>Histogram Matching Score</th><th>Plagiarism Result</th></tr>'
        result = 'No Plagiarism Detected'
        print(str(name)+" "+str(similarity))
        if similarity >= 39000:
            result = 'Plagiarism Detected'
        output+='<tr><td><font size="" color="white">'+file+'</td><td><font size="" color="white">'+name+'</td>'
        output+='<td><font size="" color="white">'+str(similarity)+'</td><td><font size="" color="white">'+result+'</td></tr>'
        context= {'data':output}
        fig, ax = plt.subplots(2,1)
        ax[0].plot(hist1, color = 'b')
        ax[1].plot(hist, color = 'g')
        plt.xlim([0, 256])
        ax[0].set_title('Original image')
        ax[1].set_title('Plagiarised image')
        plt.show()
        return render(request, 'SuspiciousImageResult.html', context)        
        

def UploadSuspiciousFileAction(request):
    if request.method == 'POST' and request.FILES['t1']:
        output = ''
        myfile = request.FILES['t1']
        fs = FileSystemStorage()
        name = str(myfile)
        filename = fs.save("test.txt", myfile)
        data = ''
        with open("test.txt", "r", encoding='iso-8859-1') as file:
            for line in file:
                line = line.strip('\n')
                line = line.strip()
                data+=line+" "
        file.close()
        os.remove("test.txt")
        data = cleanPost(data.strip().lower())
        sim = 0
        ff = 'No Match Found'
        for i in range(len(text_data)):
            similarity = LCS(text_data[i],data)
            if similarity > sim:
                sim = similarity
                ff = text_files[i]
               
        output = '<table border=1 align=center><tr><th>Source Original File Name</th><th>Suspicious File Name</th><th>LCS Score</th><th>Plagiarism Result</th></tr>'
        result = 'No Plagiarism Detected'
        similarity_percent = 0
        if sim >= 0:
            similarity_percent = sim/len(word_tokenize(data))
            if similarity_percent >= 0.60:
                result = 'Plagiarism Detected'
        output+='<tr><td><font size="" color="white">'+ff+'</td><td><font size="" color="white">'+name+'</td>'
        output+='<td><font size="" color="white">'+str(similarity_percent)+'</td><td><font size="" color="white">'+result+'</td></tr>'
        context= {'data':output}
        return render(request, 'SuspiciousFileResult.html', context)
    

def UploadSourceImage(request):
    if request.method == 'GET':
        if len(image_files) == 0:
            for root, dirs, directory in os.walk('images'):
                for j in range(len(directory)):
                    img = cv2.imread(root+"/"+directory[j])
                    img = cv2.resize(img,(200,200))
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
                    image_data.append(hist)
                    image_files.append(directory[j])
        output = '<table border=1 align=center><tr><th>Source Image File Name</th><th>Histogram Values</th></tr>'
        for i in range(len(image_files)):
            output+='<tr><td><font size="" color="white">'+image_files[i]+'</td><td><font size="" color="white">'+str(image_data[i])+"</td></tr>"
        context= {'data':output}
        return render(request, 'UploadSourceImage.html', context)

def UploadSource(request):
    if request.method == 'GET':
        if len(text_files) == 0:
            for root, dirs, directory in os.walk('corpus-20090418'):
                for j in range(len(directory)):
                    data = ''
                    with open(root+"/"+directory[j], "r", encoding='iso-8859-1') as file:
                        for line in file:
                            line = line.strip('\n')
                            line = line.strip()
                            data+=line+" "
                    file.close()
                    data = cleanPost(data.strip().lower())
                    text_files.append(directory[j])
                    text_data.append(data)
        output = '<table border=1 align=center><tr><th>Source File Name</th><th>Words in File</th></tr>'
        for i in range(len(text_files)):
            length = len(text_data[i].split(" "))
            output+='<tr><td><font size="" color="white">'+text_files[i]+'</td><td><font size="" color="white">'+str(length)+"</td></tr>"
        context= {'data':output}
        return render(request, 'UploadSource.html', context)


def UserLogin(request):
    if request.method == 'POST':
      username = request.POST.get('username', False)
      password = request.POST.get('password', False)
      index = 0
      con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = '', database = 'plagiarism',charset='utf8')
      with con:    
          cur = con.cursor()
          cur.execute("select * FROM users")
          rows = cur.fetchall()
          for row in rows: 
             if row[0] == username and password == row[1]:
                index = 1
                break		
      if index == 1:
       file = open('session.txt','w')
       file.write(username)
       file.close()   
       context= {'data':'welcome '+username}
       return render(request, 'UserScreen.html', context)
      else:
       context= {'data':'login failed'}
       return render(request, 'Login.html', context)

def Signup(request):
    if request.method == 'POST':
      username = request.POST.get('username', False)
      password = request.POST.get('password', False)
      contact = request.POST.get('contact', False)
      email = request.POST.get('email', False)
      address = request.POST.get('address', False)
      db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = '', database = 'plagiarism',charset='utf8')
      db_cursor = db_connection.cursor()
      student_sql_query = "INSERT INTO users(username,password,contact_no,email,address) VALUES('"+username+"','"+password+"','"+contact+"','"+email+"','"+address+"')"
      db_cursor.execute(student_sql_query)
      db_connection.commit()
      print(db_cursor.rowcount, "Record Inserted")
      if db_cursor.rowcount == 1:
       context= {'data':'Signup Process Completed'}
       return render(request, 'Register.html', context)
      else:
       context= {'data':'Error in signup process'}
       return render(request, 'Register.html', context)


