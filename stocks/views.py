from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.conf import settings
from .forms import BuyStockForm, SellStockForm
from .forms import UserRegistrationForm, UserInfoForm
from .models import UserInfo, UserStock, Stocks
import requests
import threading

websocket_api_key = 'd1jlie9r01qvg5gva1kgd1jlie9r01qvg5gva1l0'



@login_required
def index(request):
    return render(request, 'index.html')


def fetch_stock_data(ticker, token):
    """Fetches stock metadata and price from Tiingo API."""
    headers = {'Content-Type': 'application/json'}
    base_url = "https://api.tiingo.com/tiingo/daily/"

    try:
        metadata_resp = requests.get(f"{base_url}{ticker}?token={token}", headers=headers)
        metadata = metadata_resp.json()

        price_resp = requests.get(f"{base_url}{ticker}/prices?token={token}", headers=headers)
        price_data = price_resp.json()[0]['close']

        stock = Stocks(
            ticker=metadata['ticker'],
            name=metadata['name'],
            description=metadata['description'],
            curr_price=price_data
        )
        stock.save()
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")


def getData(request):
    """Fetch and save stock data from Tiingo API (for testing or background job)."""
    nasdaq_tickers = [
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA",
        "PEP", "INTC", "CSCO", "ADBE", "CMCSA", "AVGO", "COST", "TMUS",
        "TXN", "AMGN", "QCOM", "INTU"
    ]

    token = settings.TIINGO_API_TOKEN
    for ticker in nasdaq_tickers:
        fetch_stock_data(ticker, token)

    return HttpResponse("Stock Data Downloaded")


@login_required
def stocks(request):
    stocks = Stocks.objects.all()
    return render(request, 'market.html', {'data': stocks})


def loginView(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'login.html')


def logoutView(request):
    logout(request)
    return redirect('login')


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        info_form = UserInfoForm(request.POST, request.FILES)
        if user_form.is_valid() and info_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])  # Proper password hashing
            user.save()

            user_info = info_form.save(commit=False)
            user_info.user = user
            user_info.save()

            login(request, user)
            send_mail(
                subject="Welcome to Investing.com",
                message=f"Welcome {user.username} to our platform",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False
            )
            return redirect('index')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserRegistrationForm()
        info_form = UserInfoForm()

    return render(request, 'register.html', {
        'user_form': user_form,
        'info_form': info_form
    })



@login_required
@login_required
def buy(request, id):
    stock = get_object_or_404(Stocks, id=id)
    if request.method == 'POST':
        form = BuyStockForm(request.POST)
        if form.is_valid():
            purchase_quantity = form.cleaned_data['quantity']
            purchase_price = stock.curr_price
            user = request.user

            user_stock, created = UserStock.objects.get_or_create(
                stock=stock, user=user,
                defaults={'purchase_price': purchase_price, 'purchase_quantity': purchase_quantity}
            )
            if not created:
                total_quantity = user_stock.purchase_quantity + purchase_quantity
                total_cost = (user_stock.purchase_quantity * user_stock.purchase_price) + (purchase_quantity * purchase_price)
                user_stock.purchase_price = total_cost / total_quantity
                user_stock.purchase_quantity = total_quantity
                user_stock.save()

            send_mail(
                subject="Buy Order Successful",
                message=f"Your purchase of {stock.name} was successful.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False
            )
            return redirect('index')
        else:
            messages.error(request, "Invalid quantity.")
    else:
        form = BuyStockForm()

    return render(request, 'buy.html', {'stock': stock, 'form': form})


@login_required
@login_required
def sell(request, id):
    stock = get_object_or_404(Stocks, id=id)
    user = request.user
    try:
        user_stock = UserStock.objects.get(stock=stock, user=user)
    except UserStock.DoesNotExist:
        messages.error(request, "You don't own this stock.")
        return redirect('stocks')

    if request.method == 'POST':
        form = SellStockForm(request.POST)
        if form.is_valid():
            sell_quantity = form.cleaned_data['quantity']

            if sell_quantity > user_stock.purchase_quantity:
                messages.error(request, "You can't sell more than you own.")
            else:
                user_stock.purchase_quantity -= sell_quantity
                user_stock.save()

                send_mail(
                    subject="Sell Order Successful",
                    message=f"Your sale of {stock.name} was successful.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False
                )
                return redirect('index')
        else:
            messages.error(request, "Invalid quantity.")
    else:
        form = SellStockForm()

    return render(request, 'sell.html', {'stock': stock, 'form': form, 'user_stock': user_stock})
