from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, request
from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.conf import settings
from web3 import Web3
import json
import redis
import logging
import hashlib

from .forms import *
from .models import *

# Create your views here.

redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                   port=settings.REDIS_PORT, db=0)

logger = logging.getLogger('django')

#wallet features
address = "0xf329CE0cBE53D2b66D3113D3074b8cE5E057e446"
private_key = "0x86ad07d7614d1a4db8dc4b3f7630a5eabd934dc3649fa10fbcbb853324821e44"



def manage_bids(request):
    if request.method == 'GET':
        all_bids = {}
        hashes = redis_instance.keys("*")
        for product_id in hashes:
            all_bids[product_id.decode('utf-8')] = {}
            # my_bids[product_id.decode('utf-8')] = redis_instance.hgetall(product_id)
            # my_bids[product_id] = {}
            bids = redis_instance.hkeys(product_id)
            for bid in bids:
                all_bids[product_id.decode('utf-8')].update(
                    {bid.decode('utf-8'): redis_instance.hget(product_id, bid).decode('utf-8')})
        return all_bids

    elif request.method == 'POST':
        user_key = str(request.user)
        bid_price = float(request.POST.get('bid'))
        retrieve_product = request.POST.get('product.id')
        product = Product.objects.get(id=retrieve_product)
        minimum_price = product.base_price
        if bid_price >= minimum_price:
            # redis_instance.set(key_product, {key_user: bid_price})
            if redis_instance.hexists(retrieve_product, "highest_bid"):
                hb_value = redis_instance.hget(retrieve_product, "highest_bid")
                if bid_price > float(hb_value):
                    redis_instance.hset(retrieve_product, user_key,
                                        bid_price)  # per creare un dizionario a due livelli usare hset
                    redis_instance.hset(retrieve_product, "highest_bid", bid_price)
                    message = 'Your bid was successfully uploaded'
                else:
                    message = 'Your bid is lower than current highest bid'
            else:
                redis_instance.hset(retrieve_product, "highest_bid", bid_price)
                redis_instance.hset(retrieve_product, user_key,
                                    bid_price)
                message = 'Your bid was successfully uploaded'

        else:
            message = 'Your bid is lower than minimum price'

        messages.info(request, message)
        return redirect('store')



def end_auction(request):
    products = Product.objects.filter(end_date__lte=timezone.now())
    for product in products:
        if not product.bidding_finished:  # verifico che l'asta non sia stata già chiusa
            product_id = product.id
            bids = redis_instance.hkeys(product_id)
            highest_bid_value = redis_instance.hget(product_id, "highest_bid")
            for bid in bids[1:]:
                bid_value = redis_instance.hget(product_id, bid)
                if bid_value == highest_bid_value:
                    total_bidders = len(bids) - 1  # -1 per escludere la key highest_bid
                    data = (f"{product_id}, {bid.decode('utf-8')}, {bid_value.decode('utf-8')}, {total_bidders}")
                    #byte_data = str.encode(data)
                    product = Product.objects.get(id=product_id)
                    user = User.objects.get(username=bid.decode('utf-8'))
                    form = CreateClosedForm(request.POST)
                    if form.is_valid():
                        closed_auction = form.save(commit=False)
                        closed_auction.winner = user
                        closed_auction.winner_price = float(bid_value)
                        closed_auction.total_bidders = total_bidders
                        closed_auction.product = product
                        closed_auction.hash = None
                        closed_auction.save()
                        product.bidding_finished = True
                        product.save()
                        manage_transaction(data, product, product_id)



def show_closed(request):
    products = ClosedAuction.objects.all()
    return render(request, 'app/show_closed.html', {'products':products})



def bids_filter(all_bids, user):
    my_bids = {}
    competitors_bids = {}
    for prod in all_bids:
        my_bids[prod] = {}
        competitors_bids[prod] = {}
        for bid in all_bids[prod]:
            if bid == "highest_bid":
                my_bids[prod].update({bid: all_bids[prod][bid]})
                competitors_bids[prod].update({bid: all_bids[prod][bid]})
            if bid == user:
                my_bids[prod].update({bid: all_bids[prod][bid]})
            else:
                competitors_bids[prod].update({bid: all_bids[prod][bid]})

    return my_bids, competitors_bids



def find_highest_bid(hash):
    highest_bid = Product.objects.filter(id=hash).values_list('base_price', flat=True)[0]
    logger.debug(type(highest_bid))
    for bid in redis_instance.hkeys(hash):
        if str(bid) == "highest_bid":  # decode utf-8
            continue
        if highest_bid < float(redis_instance.hget(hash, bid)):
            highest_bid = float(redis_instance.hget(hash, bid))

    return highest_bid


@login_required(login_url='login')
def bids_summary(request):
    if request.method == 'GET':
        all_bids = manage_bids(
            request)  # alla variabile all_bids è assegnato il valore del return, altrimenti, se la funzione non avesse un valore di ritorno
        # non potremmo assegnarla a una variabile, oltre a ciò tramite la variabile richiamiamo anche la funzione menage_bids
        all_bids_tuple = bids_filter(all_bids,
                                     request.user.username)  # qui sovrascriviamo il precedente all_bids(dictionary) con il nuovo dictionary con i nomi al posto degli id
        # context = my_bids.__getitem__('context')
        logger.debug(all_bids)
        all_bids_tuple = to_names(all_bids_tuple[0]), to_names(all_bids_tuple[1])
        # return HttpResponse(all_bids)
        return render(request, 'app/cart.html', {"my_bids": all_bids_tuple[0], "competitors_bids": all_bids_tuple[1]})


@login_required(login_url='login')
def delete(request):
    user_key = str(request.user)
    prod_id = request.GET.get('prod_id')
    bid_price = redis_instance.hget(prod_id, user_key)
    redis_instance.hdel(prod_id, user_key)
    if float(bid_price) == float(redis_instance.hget(prod_id, "highest_bid")):
        redis_instance.hdel(prod_id, "highest_bid")
        redis_instance.hset(prod_id, "highest_bid", find_highest_bid(prod_id))
    messages.info(request, 'Your bid has been deleted')
    context = {}
    return render(request, 'app/cart.html', context)



def to_names(ids):
    names = {}
    for key in ids:
        prod_obj = Product.objects.get(id=key)
        prod_name = getattr(prod_obj, 'name')
        logger.debug(prod_name)
        names[(prod_name, key)] = ids[key]

    return names


@login_required(login_url='login')
def store(request):
    if request.method == 'POST':
        return manage_bids(request)

    elif request.method == 'GET':
        end_auction(request)
        products = Product.objects.all()
        context = {'products': products}

        return render(request, 'app/store.html', context)



def register_page(request):
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('username')
            messages.success(request, 'Account was created for ' + user)
            return redirect('login_page')
    context = {'form': form}
    return render(request, 'app/register.html', context)



def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')

        user = authenticate(request, username=username, password=password, email=email)

        if user is not None:
            login(request, user)
            return redirect("store")
        else:
            messages.info(request, 'Username or password is incorrect')

    context = {}
    return render(request, 'app/login.html', context)



def logout_user(request):
    logout(request)
    return redirect('login_page')



def manage_transaction(data, product, product_id):
    infura_url = "https://ropsten.infura.io/v3/de19542993aa47f98c02ebc4b5eb7bed"
    web3 = Web3(Web3.HTTPProvider(infura_url))
    nonce = web3.eth.getTransactionCount(address)
    gasPrice = web3.eth.gasPrice
    tx = {
        'nonce': nonce,
        'to': "0x0000000000000000000000000000000000000000",
        'value': web3.toWei(0, 'ether'),
        'gas': 100000,
        'gasPrice': gasPrice,
        'data': data.encode('utf-8')
    }
    signed_tx = web3.eth.account.signTransaction(tx, private_key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    relevant_product = ClosedAuction.objects.get(product=product)
    relevant_product.hash = web3.toHex(tx_hash)
    relevant_product.save()
    redis_instance.delete(product_id)



def transaction_verification(request):
    infura_url = "https://ropsten.infura.io/v3/de19542993aa47f98c02ebc4b5eb7bed"
    web3 = Web3(Web3.HTTPProvider(infura_url))
    auctions = ClosedAuction.objects.all()
    data = []
    for element in auctions:
        transaction = element.hash
        data.append(web3.eth.getTransaction(transaction))
    return HttpResponse(data)







