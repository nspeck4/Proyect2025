from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def vista_panel(request):
    return render(request, 'OrgCOntrol/dashboard.html')