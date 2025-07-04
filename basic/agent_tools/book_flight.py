import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

stripe.api_key = os.getenv("STRIPE_API_KEY")

def book_flight(flight_id: str, price: str):
    print(f"Booking flight {flight_id} for {price}...")

    try:
        amount = int(float(price.replace('$', '')) * 100)
    except ValueError as ve:
        print("Price parsing error:", ve)
        return {"error": "Invalid price format."}

    try:
        customer = stripe.Customer.create(source="tok_visa")
        charge = stripe.Charge.create(
            amount=amount,
            currency='usd',
            description=f"Flight booking for {flight_id}",
            customer=customer.id
        )
        print("Stripe charge succeeded:", charge['receipt_url'])
        return {
            "invoice_url": charge['receipt_url']
        }

    except Exception as e:
        print("Stripe error:", e)
        return {"error": f"Stripe error: {str(e)}"}