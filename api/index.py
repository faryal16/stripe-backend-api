import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import stripe
# from dotenv import load_dotenv
from mangum import Mangum

# load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe.api_key:
    raise RuntimeError("STRIPE_SECRET_KEY not set in environment variables!")

@app.post("/create-checkout-session/")
async def create_checkout_session(request: Request):
    data = await request.json()
    success_url = "https://class08-raah-e-hunar-app.streamlit.app/?payment=success"
    cancel_url = "https://class08-raah-e-hunar-app.streamlit.app/?payment=cancel"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "pkr",
                    "product_data": {"name": data["title"]},
                    "unit_amount": int(data["price"]) * 100,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=data.get("email"),
        )
        return {"checkout_url": session.url}
    except Exception as e:
        return {"error": str(e)}

@app.post("/webhook/")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e:
        return {"error": str(e)}

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print("✅ Payment successful:", session)

    return {"status": "success"}

handler = Mangum(app)  # This wraps the FastAPI app for AWS Lambda (Vercel)
