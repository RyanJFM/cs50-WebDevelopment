from django.shortcuts import render
import markdown2 
from . import util
from django.http import HttpResponseRedirect
from django.urls import reverse
from random import random

def index(request):
    return render(request, "encyclopedia/index.html", {
        "entries": util.list_entries()
    })

# entry
def entry(request, title):

    #get entry from title
    entry = util.get_entry(title)

    #if entry is None return error page
    if entry is None:
        return render(request, "encyclopedia/error.html",{
            "message" : f"page {title} not found"
        })

    #convert markdown to HTML
    entry = markdown2.markdown(entry)

    #if entry was found display it
    return render(request, "encyclopedia/entry.html", {
        "title": title,
        "entry": entry
    })

# search
def search(request):
    # get query from search
    query = request.GET.get("q")

    # if query is none redirect to index
    if query is None:
        return HttpResponseRedirect(reverse("index"))

    # get list of entries
    entries = util.list_entries()

    # check if entry exists
    for title in entries:
        if title.lower() == query.lower():

            # get contex
            contex = util.get_entry(title)

            # convert markdown to HTML
            contex = markdown2.markdown(contex)

            # return page
            return render(request, "encyclopedia/entry.html", {
                "entry":contex,
                "title": title
            })
    # if entry does not exist return search results
    request.session["matches"] = []
    for title in entries:
        if query.lower() in title.lower():
            request.session["matches"] += [title]
    return render(request, "encyclopedia/search.html", {
        "matches": request.session["matches"],
        "query": query
    })

def new_page(request):

    # if the method is GET display the HTML form
    if request.method == "GET":
        return render(request, "encyclopedia/new_page.html")

    # check if method is POST
    elif request.method == "POST":
        # get title from "form"
        title = request.POST.get("title").strip()
        
        # get content from "form"
        content = request.POST.get("content")

        # if title or content is None return to error page
        if (title is None) or (content is None):
            return render(request, "encyclopedia/error.html", {
                "message" : "Both title and content are required"
            })
        
        # if title already exists return to error page
        if title in util.list_entries():
            return render(request, "encyclopedia/error.html", {
                "message" : f"Page {title} already exists"
            })
        
        # save entry
        util.save_entry(title, content)

        # redirect to new page
        return HttpResponseRedirect(reverse("entry", kwargs={"title": title}))
    
def edit_page(request, title):

        # if the method is GET display the HTML form
        if request.method == "GET":
            content = util.get_entry(title)
            return render(request, "encyclopedia/edit_page.html", {
                "title": title,
                "content": content
            })

        # check if method is POST
        elif request.method == "POST":
            # get title from "form"
            title = request.POST.get("title").strip()
            
            # get content from "form"
            content = request.POST.get("content")

            # if title or content is None return to error page
            if (title is None) or (content is None):
                return render(request, "encyclopedia/error.html", {
                    "message" : "Both title and content are required"
                })
            
            # save entry
            util.save_entry(title, content)

            # redirect to new page
            return HttpResponseRedirect(reverse("entry", kwargs={"title": title}))

def random_page(request):
    entries = util.list_entries()
    title = entries[int(random() * len(entries))]
    return HttpResponseRedirect(reverse("entry", kwargs={"title": title}))