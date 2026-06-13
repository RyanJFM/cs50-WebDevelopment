from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import Listing, User, Comments, Bids


def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.filter(active=True)
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

def create_listing(request):
    # if method was get show page
    if request.method == "GET":
        return render(request, "auctions/create_listing.html")
    
    # if method was post create lisiting
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        starting_bid = request.POST["starting_bid"]
        image_url = request.POST["image_url"]
        category = request.POST["category"]
        owner = request.user
        listing = Listing(title=title, description=description, starting_bid=starting_bid, image_url=image_url, category=category, owner=owner)
        listing.save()
        return HttpResponseRedirect(reverse("listing", args=(listing.id,)))
    
def listing(request, listing_id):
    if request.method == "GET":
        listing = Listing.objects.get(pk=listing_id)
        if request.user.is_authenticated:
            user_watchlist = request.user.watchlist.filter(active=True)
        else:
            user_watchlist = []

        winner = None
        highest_bid = listing.bids.order_by('-bid_amount').first()
        if highest_bid is not None:
            winner = highest_bid.user
        else:
            winner = "No bids placed"

        return render(request, "auctions/listing.html", {
            "listing": listing,
            "user_watchlist": user_watchlist,
            "comments": Comments.objects.filter(listing=listing),
            "winner": winner
        })


@login_required     
def add_watchlist(request, listing_id):
    if request.method == "GET":
        listing = Listing.objects.get(pk=listing_id)
        user = request.user
        user.watchlist.add(listing)
        return HttpResponseRedirect(reverse("listing", args=(listing_id,)))

@login_required  
def remove_watchlist(request, listing_id):
    if request.method == "GET":
        listing = Listing.objects.get(pk=listing_id)
        user = request.user
        user.watchlist.remove(listing)
        return HttpResponseRedirect(reverse("listing", args=(listing_id,)))

@login_required   
def watchlist(request, user_id):
    if request.method == "GET":
        user = User.objects.get(pk=user_id)
        the_list = user.watchlist.filter(active=True)
        return render(request, "auctions/watchlist.html", {
            "watchlist": the_list
        })
    
@login_required
def add_comment(request, listing_id):
    if request.method == "POST":
        listing = Listing.objects.get(pk=listing_id)
        user = request.user
        comment_text = request.POST["comment"]
        comment = Comments(listing=listing, user=user, comment=comment_text)
        comment.save()
        return HttpResponseRedirect(reverse("listing", args=(listing_id,)))
    
@login_required
def close_listing(request, listing_id):
    if request.method == "GET":
        listing = Listing.objects.get(pk=listing_id)
        listing.active = False
        listing.save()

        for bid in listing.bids.all():
            if bid.bid_amount == listing.starting_bid:
                winner = bid.user
                break

        return render(request, "auctions/listing.html", {
            "listing": listing,
            "user_watchlist": request.user.watchlist.filter(active=True),
            "comments": Comments.objects.filter(listing=listing),
            "message": f"Listing closed winner is {winner}"
        })  

@login_required
def place_bid(request, listing_id):
    if request.method == "POST":
        listing = Listing.objects.get(pk=listing_id)
        user = request.user
        bid_amount = request.POST["bid_amount"]
        # check if bid is valid
        if int(bid_amount) <= int(listing.starting_bid):
            return render(request, "auctions/listing.html", {
                "listing": listing,
                "user_watchlist": request.user.watchlist.filter(active=True),
                "comments": Comments.objects.filter(listing=listing),
                "message": "Bid must be higher than starting bid."
            })
        # if valid save bid and update listing
        listing.starting_bid = bid_amount
        listing.save()
        bids = Bids(listing=listing, user=user, bid_amount=bid_amount)
        bids.save()
        return HttpResponseRedirect(reverse("listing", args=(listing_id,)))