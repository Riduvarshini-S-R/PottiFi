from threading import local
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.http import HttpResponse 
from django.contrib import auth  
import pyrebase
from pyrebase.pyrebase import Storage
from requests.adapters import Retry
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import random

from requests.api import post
from requests.sessions import session
cred = credentials.Certificate("ProjectPottiFi/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

firebaseconfig={
    'apiKey': "AIzaSyDL8ylTtR7BB-x1ylyTyfPGq_JvVKnNsNM",
    'authDomain': "projectpottifi.firebaseapp.com",
    'databaseURL': "https://projectpottifi-default-rtdb.asia-southeast1.firebasedatabase.app",
    'projectId': "projectpottifi",
    'storageBucket': "projectpottifi.appspot.com",
    'messagingSenderId': "999007637635",
    'appId': "1:999007637635:web:3b9545dc86eef5f31ccbb6",
    'measurementId': "G-FRD0ZCK6PR"
}

firebase=pyrebase.initialize_app(firebaseconfig)
db=firebase.database()
firestoredb=firestore.client()
storage=firebase.storage()
authe=firebase.auth()


def home(request):
    if request.method=='POST':
        mailid=request.POST.get('mailid')
        password=request.POST.get('password')
        try:
            user=authe.sign_in_with_email_and_password(mailid,password)
            session_id=user['idToken']
            request.session['uid']=str(session_id)
            return redirect('/main/')
        except:
            message="invalid credentials"
            return render(request,'home.html', {'message' : message } )
    return render(request,'home.html')
def main(request):
    tokenid=request.session['uid']
    userid=authe.get_account_info(tokenid)['users'][0]['localId']

    userdata=firestoredb.collection('users').document(userid).get()

    stage=firestoredb.collection('stages').document(userid)
    stages=stage.get().to_dict()
    stagedetails={}
    try:
        for i in stages['ongoingstages']:
            stagedetail=firestoredb.collection(i).document('stagedetails').get().to_dict()
            stagedetails[i]=stagedetail
    except:
        pass
    return render(request,'main.html',{'stagedetails':stagedetails})

def signup(request):
    
    if request.method=='POST':
        firstname=request.POST['firstname']
        lastname=request.POST['lastname']
        mailid=request.POST['mailid']
        password1=request.POST['password1']
        password2=request.POST['password2']
        if password1==password2:
            try:
                user=authe.create_user_with_email_and_password(mailid,password1)
                userid=user['localId']
                print(userid)
                user_details={'firstname':firstname,'lastname':lastname,'emailid':mailid,'password':password1}
                firestoredb.collection('users').document(userid).set(user_details)
            except:
                message="EMAIL-ID ALREADY EXIST"
                return render(request,'home.html',{ 'message' : message } )
            return render(request,'main.html')
        else:
            message="PASSWORDS DOES NOT MATCH"
            return render(request,'home.html',{'message':message})


def logout(request):
    auth.logout(request)
    return redirect('/')

def codegenerator():
    stagecode=random.randint(1000,9999)
    stagecodesinuse=firestoredb.collection('stagecodes').document('stagecodesinuse').get().to_dict()

    while str(stagecode) in stagecodesinuse['codes']:
        stagecode=random.randint(1000,9999)
    stagecode=str(stagecode)
    try:
        firestoredb.collection('stagecodes').document('stagecodesinuse').update({'codes': firestore.ArrayUnion([stagecode])})
    except:
        firestoredb.collection('stagecodes').document('stagecodesinuse').set({'codes': firestore.ArrayUnion([stagecode])})

    return stagecode

def createpage(request):
    tokenid=request.session['uid']
    userid=authe.get_account_info(tokenid)['users'][0]['localId']
    userdata=firestoredb.collection('users').document(userid).get().to_dict()

    if request.method=='POST':
        eventtitle=request.POST['eventtitle']
        eventtheme=request.POST['eventtheme']
        participantlimit=request.POST['participantlimit']
        individualentrylimit=request.POST['individualentrylimit']
        judgescount=request.POST['judgescount']
        judgename=request.POST['judgename']
        submissionstartdate=request.POST['submissionstartdate']
        submissionclosedate=request.POST['submissionclosedate']
        resultdate=request.POST['resultdate']  


        stagedata={'eventtitle': eventtitle,'eventtheme': eventtheme ,'participantlimit': int(participantlimit) ,
                    'individualentrylimit': int(individualentrylimit)  ,'judgescount': int(judgescount) ,
                    'judgename': judgename,'submissionstartdate': submissionstartdate ,
                    'submissionclosedate': submissionclosedate ,'resultdate': resultdate }        
            
        stagecode=codegenerator()
        
        firestoredb.collection(stagecode).document('hostdetails').set({'userid':userid})
        firestoredb.collection(stagecode).document('stagedetails').set(stagedata)


        try:
            firestoredb.collection('stages').document(userid).update({'ongoingstages': firestore.ArrayUnion([stagecode])})
        except:
            firestoredb.collection('stages').document(userid).set({'ongoingstages': firestore.ArrayUnion([stagecode])})
        message="Stage Created Successfully"
        return render(request,'main.html',{'message': message})          
    return render(request,'createstage.html')

def stage(request,stagecode):

    tokenid=request.session['uid']
    userid=authe.get_account_info(tokenid)['users'][0]['localId']

    stage=firestoredb.collection('stages').document(userid).collection(stagecode).document('stagedetails').get().to_dict()
    

    return render(request,'stage.html',{'stagedetails':stage,'stagecode':stagecode})


def hostprofile(request):
    tokenid=request.session['uid']
    userid=authe.get_account_info(tokenid)['users'][0]['localId']
    userdata=firestoredb.collection('users').document(userid).get().to_dict()
    return render(request,'hostprofile.html',{'userdata':userdata})


def participateup(request,stagecode):
    if request.method=='POST':
        firstname=request.POST['firstname']
        lastname=request.POST['lastname']
        mailid=request.POST['mailid']
        password1=request.POST['password1']
        password2=request.POST['password2']
        if password1==password2:
            mailids=firestoredb.collection(stagecode).document('mailids').get().to_dict()
            if mailid not in mailids['pmailids']:
                try:
                    firestoredb.collection(stagecode).document('mailids').update({'pmailids': firestore.ArrayUnion([mailid])})
                except:
                    firestoredb.collection(stagecode).document('mailids').set({'pmailids': firestore.ArrayUnion([mailid])})
                user_details={'firstname':firstname,'lastname':lastname,'emailid':mailid,'password':password1}
                firestoredb.collection(stagecode).document('participants').collection(mailid).document('parcipantdetails').set(user_details)
                return redirect('/')
            else:
                message="mail_id already exist"
                return render(request,'participateup.html',{'message':message,'stagecode':stagecode})      
        else:
            message="passwords does not match"
            return render(request,'participateup.html',{'message':message,'stagecode':stagecode})    

    return render(request,'participateup.html',{'stagecode':stagecode})
def individualsubmission(request):
    if request.method=='POST' and len(request.POST['stagecode'])!=0:
        stagecode=request.POST['stagecode']
        mailid=request.POST['mailid']
        password=request.POST['password']
        try:
            mailids=firestoredb.collection(stagecode).document('mailids').get().to_dict()
            if mailid in mailids['pmailids']:
                participantdetails=firestoredb.collection(stagecode).document('participants').collection(mailid).document('participantdetails').get().to_dict()
                stagedetails=firestoredb.collection(stagecode).document('stagedetails').get().to_dict()
                if password==participantdetails['password']:
                    request.session['pid']=str(mailid)
                    return render(request,'submission.html',{'participantdetails':participantdetails,'stagedetails':stagedetails})
                else:
                    message="invalid credentials"
                    return render(request,'home.html', {'message' : message } )
            else:
                message="mailid does not exist; get in stage by registering"
                return render(request,'participateup.html', {'message' : message } )
        except:
            message="stage does not exist"
            return render(request,'home.html',{'message':message})
    if request.method=='POST':
        file=request.POST['imagefile']
        storage.add('file1')
    return render(request,'submission.html')

def submitphoto(request):
    pass