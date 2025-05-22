import stripe
import os
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_API_KEY")

def book_flight(flight_id: str, price: str):
    print(f"[book_flight] Called with: flight_id={flight_id}, price={price}")

    try:
        amount = int(float(price.replace('$', '')) * 100)
    except ValueError:
        result = {"status": "error", "message": "Invalid price format."}
        print(f"[book_flight] Returning: {result}")
        return result

    try:
        customer = stripe.Customer.create(source="tok_visa")
        charge = stripe.Charge.create(
            amount=amount,
            currency='usd',
            description=f"Flight booking for {flight_id}",
            customer=customer.id
        )

        result = {
            "status": "success",
            "invoice_url": charge["receipt_url"],
            "flight_id": flight_id,
            "price": price
        }
        print(f"[book_flight] Returning: {result}")
        return result

    except Exception as e:
        result = {"status": "error", "message": f"Booking failed: {str(e)}"}
        print(f"[book_flight] Returning: {result}")
        return result