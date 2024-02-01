from django.shortcuts import render
import uuid

def index(request):
    return render (request, 'autogen_chat/index.html', {'session_id': uuid.uuid4()})
