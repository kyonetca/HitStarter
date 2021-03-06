from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.http import Http404
from django.conf import settings
from django.conf import settings as django_settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response, Http404, HttpResponse
from django.template import loader, RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST 
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic.base import TemplateView
from django.db import connection, transaction

from hitstarter.apps.site.models import Project
import hitstarter.apps.site.models as projects

import random
import requests
import stripe

def home(request):

    featured_projects = projects.get_featured_projects()

    return render_to_response('index.html', {
        'projects': featured_projects,
        'home': True,
        'is_onion': is_onion(request)
        },
        context_instance=RequestContext(request))

def project(request, project_id):

    if request.POST:
        return HttpResponse("GET out of here!")

    project = projects.get_project_by_id(project_id)

    raised = (project.stripe_amount / 7500) + project.btc_amount

    if random.randrange(0,9) < 1:
        res  = requests.get('https://coinbase.com/api/v1/account/balance?api_key=%s' % settings.COINBASE_API_KEY)     
        try:
            raised = res.json()['amount']
            raised = raised + (project.stripe_amount / 7500)

            project.btc_amount = res.json()['amount']
            project.save()
        except Exception, e:
            pass

    if django_settings.DEBUG:
        api_key = settings.STRIPE_DEBUG_API_KEY
    else:
        api_key = settings.STRIPE_API_KEY

    percent = (float(raised)/float(project.target)) * 100       

    return render_to_response('project.html', {
            'project': project,
            'raised': raised,
            'percent': percent,
            'is_onion': is_onion(request),
            'api_key': api_key
        },
        context_instance=RequestContext(request))

def fund_project(request, project_id):

    project = projects.get_project_by_id(project_id)

    if django_settings.DEBUG:
        stripe.api_key = settings.STRIPE_DEBUG_API_SECRET_KEY
    else:
        stripe.api_key = settings.STRIPE_API_SECRET_KEY

    # Get the credit card details submitted by the form
    try:
        token = request.POST['stripeToken']
        value = request.POST['fundValue']
    except Exception, e:
        return HttpResponseRedirect('/p/' + str(project.pk) + '/' + project.slug)

    # Create the charge on Stripe's servers - this will charge the user's card
    try:
        charge = stripe.Charge.create(
            amount= int(float(value)), # amount in CENTS, again
            currency="usd",
            card=token,
            description="Anonymous Donation to " + project.title
        )
    except stripe.CardError, e:
        # The card has been declined
        return HttpResponse("Payment declined! :( Please try again!")


    project.stripe_amount = project.stripe_amount + int(float(value))
    project.save()

    raised = '0'
    res  = requests.get('https://coinbase.com/api/v1/account/balance?api_key=%s' % settings.COINBASE_API_KEY)     
    try:
        raised = res.json()['amount']
        raised = raised + project.stripe_amount / 7500
    except Exception, e:
        raised = 0 + (project.stripe_amount / 7500)

    percent = (float(raised)/float(project.target)) * 100       

    return render_to_response('project.html', {
            'project': project,
            'raised': raised,
            'percent': percent,
            'is_onion': is_onion(request),
            'message': "Success! Thank you for supporting this project."
        },
        context_instance=RequestContext(request))

def about(request):

    return render_to_response('about.html', {
        'is_onion': is_onion(request)
        },
        context_instance=RequestContext(request))

def is_onion(request):
    if 'htstrtc3uttwk4li.onion' == request.META['HTTP_HOST'].strip():
        return True
    else:
        return False