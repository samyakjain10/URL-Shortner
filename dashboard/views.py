from django.shortcuts import render, redirect
import random
import sympy
import time
import numpy as np
from django.contrib.auth.decorators import login_required

from .models import ShortenedURL

import math
import mmh3
from bitarray import bitarray

from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
import httplib2
import pandas as pd

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
KEY_FILE_LOCATION = r'C:\Users\Jain\Desktop\urlshortener\dashboard\client_secrets.json'
VIEW_ID = '233035039'

class BloomFilter(object):
 
    def __init__(self, items_count, fp_prob):
        
        self.fp_prob = fp_prob
        self.size = self.get_size(items_count, fp_prob)
        self.hash_count = self.get_hash_count(self.size, items_count)
        self.bit_array = bitarray(self.size)
        self.bit_array.setall(0)
 
    def add(self, item):
        
        digests = []
        for i in range(self.hash_count):
            digest = mmh3.hash(item, i) % self.size
            digests.append(digest)
 
            self.bit_array[digest] = True
 
    def check(self, item):
        
        for i in range(self.hash_count):
            digest = mmh3.hash(item, i) % self.size
            if self.bit_array[digest] == False:
                return False
        return True
 
    @classmethod
    def get_size(self, n, p):
        m = -(n * math.log(p))/(math.log(2)**2)
        return int(m)
 
    @classmethod
    def get_hash_count(self, m, n):
        k = (m/n) * math.log(2)
        return int(k)

def genCode():
    rands = list(range(48, 58)) + list(range(65, 91)) + list(range(97, 123))
    code = ''
    while len(code) < 8:
        code += chr(random.choice(rands))
    return code

def shorten( url, request):
    results = ShortenedURL.objects.all()
    fil = BloomFilter(200000, 0.05)
    
    for item in results:
        fil.add(item.short_code)
    
    notFound = True
    code = ''

    while notFound == True:
        code = genCode() #Generate Random Code Corresponding to the URL
        notFound = fil.check(code)
    fil.add(code)
 
    entry = ShortenedURL(short_code=code, original_url=url, owner=request.user)
    entry.save()

def initialize_analyticsreporting():
  """Initializes an Analytics Reporting API V4 service object.

  Returns:
    An authorized Analytics Reporting API V4 service object.
  """
  credentials = ServiceAccountCredentials.from_json_keyfile_name(
      KEY_FILE_LOCATION, SCOPES)

  # Build the service object.
  analytics = build('analyticsreporting', 'v4', credentials=credentials)

  return analytics


def get_report(analytics,url):
  """Queries the Analytics Reporting API V4.

  Args:
    analytics: An authorized Analytics Reporting API V4 service object.
  Returns:
    The Analytics Reporting API V4 response.
  """
  if url=="":
    return analytics.reports().batchGet(
        body={
          'reportRequests': [
          {
            'viewId': VIEW_ID,
            'metrics': [
              {'expression': 'ga:sessions'},
              {'expression': 'ga:pageviews'},
              {'expression': 'ga:uniquePageviews'},
              {'expression': 'ga:newUsers'}
            ],
            'dateRanges': [{'startDate': '30daysAgo', 'endDate': 'today'}],
            'dimensions': [{'name': 'ga:country'}]
          }]
        }
    ).execute()

  else:
    return analytics.reports().batchGet(
        body={
          'reportRequests': [
          {
            'viewId': VIEW_ID,
            "filtersExpression": "ga:pagePath=@"+url,
            'metrics': [
              {'expression': 'ga:sessions'},
              {'expression': 'ga:pageviews'},
              {'expression': 'ga:users'},
              {'expression': 'ga:avgRedirectionTime'}
            ],
            'dateRanges': [{'startDate': '30daysAgo', 'endDate': 'today'}],
            'dimensions': [{'name': 'ga:country'}]
          }]
        }
    ).execute()

def get_response(response):
  """Parses and prints the Analytics Reporting API V4 response.

  Args:
    response: An Analytics Reporting API V4 response.
  """

  output = {}

  for report in response.get('reports', []):
    columnHeader = report.get('columnHeader', {})
    dimensionHeaders = columnHeader.get('dimensions', [])
    metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])

    for row in report.get('data', {}).get('rows', []):
      dimensions = row.get('dimensions', [])
      dateRangeValues = row.get('metrics', [])

      # for header, dimension in zip(dimensionHeaders, dimensions):
      #   print(header + ': ', dimension)

      for i, values in enumerate(dateRangeValues):
        # print('Date range:', str(i))
        for metricHeader, value in zip(metricHeaders, values.get('values')):
          output[metricHeader.get('name')] = value

  return output

@login_required(login_url='login')
def dashboard(request):
    
  if request.method == "POST":
      url = request.POST.get('url')
      shorten(url, request)
  context = ShortenedURL.objects.filter(owner=request.user)
  context = {
    'links' : context
  }
  return render(request,'dashboard/index.html', context)

@login_required(login_url='login')
def linkDashboard(request, short_code):
  
  analytics = initialize_analyticsreporting()
  url = short_code
  response = get_report(analytics,url)
  output = get_response(response)
  # print(output)
  context = ShortenedURL.objects.filter(owner=request.user)

  #Dictionary is not empty
  if output: 
    context = {
      'links' : context,
      'session' : output['ga:sessions'],
      'views' : output['ga:pageviews'],
      'users' : output['ga:users'],
      'avgPageLoadTime' : output['ga:avgRedirectionTime'],
    }

  #Dictionary is empty
  #Implies no data (no views)
  else:
    context = {
      'links' : context,
      'session' : 0,
      'views' : 0,
      'users' : 0,
      'avgPageLoadTime' : 0,
    }

  return render(request,'dashboard/index.html', context)

@login_required(login_url='login')
def linkDelete(request, short_code):
  
  ShortenedURL.objects.filter(short_code=short_code).delete()
  return redirect('/dashboard')




