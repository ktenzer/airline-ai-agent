import stripe
import os
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_API_KEY")

def book_flight(flight_id: str, price: str):
    print(f"Booking flight {flight_id} for {price}...")
    try:
        amount = int(float(price.replace('$', '')) * 100)
    except ValueError:
        return {"error": "❌ Invalid price format."}

    try:
        customer = stripe.Customer.create(source="tok_visa")
        charge = stripe.Charge.create(
            amount=amount,
            currency="usd",
            description=f"Flight booking for {flight_id}",
            customer=customer.id,
        )
        return {"invoice_url": charge.receipt_url}
    except Exception as e:
        return {"error": f"❌ Stripe error: {str(e)}"}