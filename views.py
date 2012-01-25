from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, RequestContext, loader
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404

from signbank.pages.views import page

def index(request):
    # TODO: test whether this page exists and use a default if not.
    return page(request, '/')
 