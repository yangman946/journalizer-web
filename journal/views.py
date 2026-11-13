from django.shortcuts import render, redirect
from django.conf import settings
import json
from datetime import date, datetime
from django.urls import reverse
from journal.services.EntryManager import fileManager, Crypto
from django.contrib.auth import views as auth_views, authenticate, login as auth_login, logout as auth_logout
from pathlib import Path
from django.contrib.auth.decorators import login_required

month_ref = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December"
]


# Create your views here.
@login_required
def home(request):

    year = date.today().year

    f = fileManager()


    years = f.getEntry()

    firstyear = years[0]
    lastyear = years[-1]

    month_firstL = f.getEntry(0)
    month_lastL = f.getEntry(len(years)-1)

    mf = month_firstL[0]
    mL = month_lastL[-1]

    day_firstL = f.getEntry(0, 0)
    day_lastL = f.getEntry(len(years)-1, len(month_lastL)-1)

    df = day_firstL[0].removesuffix('.txt')
    dL = day_lastL[-1].removesuffix('.txt')

    #print(years)
    months = f.getEntry(len(years)-1)
    daysz = f.getEntry(0, 0) # this month



    x = {}

    for i in range(len(years)): #loop through years
        
        months = f.getEntry(i) # get all the montsh of given year
        for e in range(len(months)): #loop through all the months
            days = f.getEntry(i, e)
            y = []
            for a in days:
                y.append(a.removesuffix(".txt"))
            month_section = {
                f'{month_ref[int(months[e])-1]}/{years[i]}': len(y),
            }
            x.update(month_section)

    #print(x)
    limit = 12
    if len(x) > limit:
        last_x = dict(list(x.items())[:limit])
    else:
        last_x = x
    print(last_x)


  


    
    #entry_directory = settings.JOURNAL_DATA_DIR / str(year)
    
    entry_dates = f.allEntries()
    #print(entry_dates)
    context = {
        'title': 'Secure Journal',
        'message': 'Welcome to your journal.',
        "entry_dates": entry_dates,
        "Timeline": dict(reversed(last_x.items())),
        "nav": [{'title': 'home', 'url': ''}],
        "totalEntries": str(len(entry_dates)),
        "DateOfFirst": f"{mf}/{firstyear}",
        "DateOfLast": f"{mL}/{lastyear}",
        "EntriesThisMonth": len(daysz),
        "latestEntry": f"/archieve/{firstyear}/{month_ref[int(mf)-1]}/{df}"
    }

    return render(request, 'journal/home.html', context)

@login_required
def write(request):

    if request.method == 'POST':
        # Fetch the textbox value. Returns None if it doesn't exist.
        user_input = request.POST.get('entryForm', None) 
        if Crypto().checkFile(): # determine whether encryption is enabled
            all_text = Crypto().code(user_input, True).decode('utf-8')

        yearx, month, formatted_date = fileManager().saveEntry(all_text)   
        Newcontent, Newyearind, Newmonthind, Newdayind = fileManager().find(yearx, month, formatted_date)

        file = Path(fileManager().getEntry(Newyearind, Newmonthind, Newdayind))
        xm = month_ref[int(file.parent.name)-1]
        ym = file.parent.parent.name
        name = file.name.removesuffix(".txt")
        return redirect('read', xyear = ym, xmonth = xm, id = name)
        
    # check if we already wrote something today...

    

    context = {
        'title': 'Write in journal',
        'message': 'Welcome to your journal.',
        'readonly': False,
        'placeholder': '',
        'date': '',
        'next': '',
        'nextMonth': '',
        'nextYear': '',
        'prev': '',
        'prevMonth': '',
        'prevYear': '',
        'invalid': fileManager().todayExists(),
        "nav": [{'title': 'home', 'url': reverse("home")}, {'title': 'write', 'url': ''}]
    }
    return render(request, 'journal/entrybase.html', context)

@login_required
def read(request, xyear, xmonth, id):
    # id is the date title in journalizer format
    month = None
    year = None
    next = None
    prev = None
    s = None
    mI = month_ref.index(xmonth)+1
    # lets fetch the file based on its ID
    path = fileManager().findEntry(id, str(mI), xyear) 
    if path != None:
        content = fileManager().getContent(path)

        if Crypto().checkFile(): # determine whether encryption is enabled

            clean_text = content[1].strip()
            # 2. Check if the user pasted the "b'...' " wrapper, and strip it out
            if clean_text.startswith("b'") and clean_text.endswith("'"):
                clean_text = clean_text[2:-1]
            elif clean_text.startswith('b"') and clean_text.endswith('"'):
                clean_text = clean_text[2:-1]

            token_bytes = clean_text.encode('ascii')
            s = Crypto().code(token_bytes, False) # decrypt


            # get previous and next urls
            formattedpath = Path(path)
            month = formattedpath.parent.name
            year = formattedpath.parent.parent.name


            yind, mind, dind = fileManager().date2ind(year, month, formattedpath.name)

            days = fileManager().getEntry(yearind=yind, monthind=mind)

            # find next entry: next means going back in time hence prev is used as variable name
            if dind + 1 > len(days) - 1: # are we the last entry of the month?
                Xmonths = fileManager().getEntry(yearind=yind) # get months of the year
                if mind + 1 > len(Xmonths) - 1: # if we exceeded the month count of this year
                    Xyears = fileManager().getEntry() # get all years
                    if yind + 1 > len(Xyears) - 1: # if we exceeded the year count 
                        # failed
                        prev = None
                    else:
                        prev = [yind+1, 0, 0]
                else:
                    prev = [yind, mind+1, 0]
            else:
                prev = [yind, mind, dind+1]

            # find previous entry: going forward in time 
        
            if dind - 1 < 0:
                if mind - 1 < 0:
                    if yind - 1 < 0:
                        next = None 
                    else:
                        m = len(fileManager().getEntry(yearind=yind-1))-1
                        next = [yind-1, m, len(fileManager().getEntry(yearind=yind-1, monthind=m))-1]
                else:
                    next = [yind, mind-1, len(fileManager().getEntry(yearind=yind, monthind=mind-1))-1]
            else:
                next = [yind, mind, dind-1]

            
        else:
            s = content

    if next != None:
        file = Path(fileManager().getEntry(next[0], next[1], next[2]))

        NextEntryMonth = month_ref[int(file.parent.name)-1]
        NextEntryYear = file.parent.parent.name
        #print(f"{NextEntryYear} - D")
        NextEntry = file.name.removesuffix(".txt")
    else:
        NextEntry = ''
        NextEntryMonth = ''
        NextEntryYear = ''

    if prev != None:
        file = Path(fileManager().getEntry(prev[0], prev[1], prev[2]))
        PreviousEntryMonth = month_ref[int(file.parent.name)-1]
        PreviousEntryYear = file.parent.parent.name
        PreviousEntry = file.name.removesuffix(".txt")
    else:
        PreviousEntry = ''
        PreviousEntryYear = ''
        PreviousEntryMonth = ''

    #raise Exception(f"Debug checkpoint.")
    #raise Exception(f"next entry year: {NextEntryYear} | Previous entry year: {PreviousEntryYear}")

    context = {
        'title': 'Read entry',
        'message': 'Welcome to your journal.',
        'readonly': True,
        'placeholder': s,
        'date': content[0],
        'next': PreviousEntry,
        'nextMonth': PreviousEntryMonth,
        'nextYear': PreviousEntryYear,
        'prev': NextEntry,
        'prevMonth': NextEntryMonth,
        'prevYear': NextEntryYear,
        'invalid': False,
        "nav": [{'title': 'home', 'url': reverse("home")}, {'title': 'archieve', 'url': reverse("archieve")}, {'title': str(id), 'url': ''}]
    }
    return render(request, 'journal/entrybase.html', context)


@login_required
def archieve(request):

    f = fileManager()
    years = f.getEntry() # list of years


    d = {}

    for i in range(len(years)): #loop through years
        x = {}
        months = f.getEntry(i) # get all the montsh
        for e in range(len(months)): #loop through all the months
            days = f.getEntry(i, e)
            y = []
            for a in days:
                y.append(a.removesuffix(".txt"))
            month_section = {
                f'{month_ref[int(months[e])-1]}': y,
            }
            x.update(month_section)
        year_section = {
            f'{years[i]}': x
        }
        d.update(year_section)

    print(d)

    context = {
        'title': 'Archieves',
        'message': 'Welcome to your journal.',
        'dict': d,
        "nav": [{'title': 'home', 'url': reverse("home")}, {'title': 'archieve', 'url': ''}]
    }
    return render(request, 'journal/archieve.html', context)


def login(request):

    context = {
        'title': 'Login',
        'message': 'Welcome to your journal.',
    }

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Returns the User object if valid, or None if invalid
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Login was successful: start the session and redirect
            auth_login(request, user)

            c = Crypto(password)
            # create crypto object
            return redirect("home")
        
        c = Crypto()
        c.lock()
        return render(request, "journal/login.html", {
            "error": "Invalid username or password"
        })
    
    return render(request, "journal/login.html", context)


def logout_view(request):
    c = Crypto()
    c.lock()
    auth_logout(request)
    return redirect("login")

@login_required
def handler_404(request, *args, **argv):
    data = {"title": "Page not found"}
    return render(request,'journal/404.html', data)