from django.shortcuts import render, redirect

from dashboard.models import ShortenedURL

def redirectToWebsite(request, short_code):
    link = ShortenedURL.objects.get(short_code=short_code)
    # return redirect(link.original_url)
    context = { "link" : link.original_url}
    return render(request, 'index.html', context)
