**Persona:** Mostafa, 34, owner of a padel court in Sheikh Zayed.

He has **two courts**, and bookings currently happen through WhatsApp with Mostafa answering them himself. His evenings are busy while mornings are underused. The page identifies problems with customers booking and not showing up, unused morning capacity, and difficulty knowing who is actually attending when regular customers bring other people.

### Required product mechanic

The stated flow is:

**Pay → Reserve → Redeem**

More specifically, the user must:

1. Pick an **available court and time slot**.
2. Pay.
3. Receive a **booking pass or code**.
4. Staff must be able to **look up that pass/code**.
5. Staff must be able to **redeem it on site once**.

### Challenge-specific constraints

The critical requirement is preventing **double booking**:

**Two people must never end up holding the same slot.**

Your product therefore has to determine:

- when the slot becomes held;
- when a held slot is released;
- what happens to the slot if payment fails partway through the process.

The page does not prescribe a particular locking algorithm, database, timeout length, QR code format, calendar system, dynamic-pricing model, or authentication system.

---

# Global Rules and Constraints Applied to ALL 5 Challenges

The page contains requirements before the challenge descriptions and then a separate section titled **“Three rules.”** Taken together, these are the explicit global requirements.

## 1. Every solution must contain a working Paymob checkout

Every build has to implement a **working end-to-end Paymob checkout using the test credentials supplied at the event**. Paymob is not supposed to be represented by a fake payment screen; it is the actual payment layer around which the product mechanic operates.

The product is expected to perform meaningful logic around payment—for example, calculating or holding something beforehand and then unlocking, issuing, reserving, or queueing something after successful payment. The exact behavior depends on the selected challenge.

---

## 2. The application must be reachable from the public internet

Paymob needs to call your application's webhook.

Therefore, **localhost alone is not sufficient**. The application must either:

- be deployed publicly; or
- expose the local server through a tunnel.

The page gives examples including **ngrok, Cloudflare Tunnel, and localtunnel**. The resulting public callback URL must be registered with Paymob.

---

## 3. Payment confirmation must come from the Paymob callback

You cannot consider an order paid simply because the customer's browser reached a successful-payment redirect page.

The page explicitly requires the application to:

- receive Paymob's callback;
- **verify the callback HMAC**;
- treat the **verified successful callback** as the point at which the order becomes paid.

This applies regardless of which of the five challenge mechanics you choose.

---

## 4. You must use Cursor during development

Cursor is explicitly part of the Build-a-thon.

The page tells participants to use it for activities including:

- planning;
- scaffolding;
- debugging;
- testing.

In particular, it mentions debugging the payment callback and writing tests around the confirmed-payment path. Judges may ask how Cursor affected the team's development speed.

### AI inside the product is NOT required

This distinction is explicit:

**You do not need to put AI into the end-user product.**

Using Cursor for development is required, but an AI feature inside the application is optional and **cannot substitute for actually implementing the selected product mechanic**.

---

## 5. It must be a working product, not a mocked payment prototype

The third official rule is **“Ship a real product.”**

The page explicitly asks for:

- a **real name**;
- **real pricing logic**;
- a **working Paymob checkout**;
- a **confirmed payment flow**.

It explicitly disallows:

- fake checkout screens;
- placeholder payment states.

So, for example, a button that simply says “Payment successful” and changes a database field without going through Paymob would not satisfy the stated rules.

## Fully by Paymob

- [x]  **Reliable payment confirmation:** A booking must not be considered paid merely because the customer's browser reaches a successful-payment page.
- [x]  **Invalid or forged payment callbacks:** Payment confirmation must not be accepted from an unverified callback.
- [x]  **Connecting payment to the correct reservation:** A confirmed payment needs to correspond to the correct booking rather than incorrectly affecting another reservation.
- [x]  **Real payment processing:** The product cannot rely on fake checkout screens, placeholder payment states, or manually simulated successful payments.

---

## Partially by Paymob

- [ ]  **Customer no-shows:** Customers can book a court and then fail to attend.
- [ ]  **Wasted court capacity from no-shows:** Reserved slots can remain unused when customers do not show up.
- [ ]  **Unclear slot status while payment is in progress:** The booking process must account for what happens to a slot between a customer's selection of it and completion of payment.
- [ ]  **Abandoned or incomplete payments:** A slot must not remain unavailable indefinitely when a customer starts the booking/payment process but does not complete it.
- [ ]  **Failed payments:** The booking process must correctly handle the slot when payment fails partway through the reservation process.
- [ ]  **Proving that a customer has a valid paid booking:** After payment, there must be a reliable way to identify the customer's valid reservation.
- [ ]  **Public accessibility for payment callbacks:** A system running only on localhost cannot receive Paymob's external callback.
- [ ]  **End-to-end booking/payment consistency:** The reservation state and payment state must remain consistent throughout the complete booking process.

---

## Fully unrelated to Paymob

- [ ]  **Manual booking management:** Mostafa currently handles court bookings himself through WhatsApp.
- [ ]  **High booking-management workload:** Mostafa has to personally respond to customers and manage reservations while operating the padel court.
- [ ]  **Uneven court utilization:** Evening slots are busy while morning slots are underused.
- [ ]  **Difficulty identifying actual attendees:** Mostafa cannot easily know who is actually attending when regular customers bring other people.
- [ ]  **Need to know which courts and time slots are actually available:** Customers must not be able to reserve a court/time combination that is unavailable.
- [ ]  **Risk of double booking:** Two customers must never end up holding the same court and time slot.
- [ ]  **Concurrency during booking:** The system must correctly handle cases where multiple customers attempt to reserve the same slot at approximately the same time.
- [ ]  **Staff verification of bookings:** On-site staff need to be able to determine whether a presented booking is valid.
- [ ]  **Preventing repeated use of the same booking:** A valid booking must not be successfully redeemed more than once.
- [ ]  **Distinguishing redeemed from unredeemed bookings:** Staff need to know whether a booking has already been used.

## Core MVP Solution

Build a **self-service padel booking web app** with two sides:

- **Customer Booking Page:** customers view available courts and time slots, select one, confirm the booking, and receive a unique **QR booking pass**.
- **Staff Check-in Page:** staff scan the QR code or enter its short code to verify the reservation and **redeem it once**.

The booking database itself acts as the **single source of truth** for availability, reservations, and redemption status.

### 1. Manual booking management

**Problem:** Mostafa currently handles court bookings himself through WhatsApp.

**Solution:**

Provide customers with a simple booking page where they can:

**Select date → Select Court 1 or Court 2 → Select available time → Confirm booking → Receive QR pass**

Bookings are created automatically without Mostafa manually answering or recording them.

---

### 2. High booking-management workload

**Problem:** Mostafa has to personally respond to customers and manage reservations.

**Solution:**

Automate the entire reservation workflow. Once a customer books, the system automatically:

- records the reservation;
- removes the slot from availability;
- generates the booking pass;
- makes the reservation visible to staff.

Mostafa only needs a simple dashboard showing today's bookings rather than manually managing conversations.

---

### 3. Uneven court utilization

**Problem:** Evening slots are busy while morning slots are underused.

**Solution:**

Clearly highlight underused morning slots inside the booking interface with labels such as:

**☀️ Morning Available**

and place them before evening slots when customers browse availability.

This gives less-used slots greater visibility without introducing additional pricing, discounting, or marketing mechanics outside the stated problem.

---

### 4. Difficulty identifying actual attendees

**Problem:** Mostafa cannot easily know who is actually attending when regular customers bring other people.

**Solution:**

Before confirming the reservation, require the booking customer to enter the **names of the attendees**.

The booking therefore contains:

**Booker + Attendee names + Court + Time**

When staff verify the booking, they can see the expected attendees instead of only knowing who originally made the reservation.

---

### 5. Need to know which courts and time slots are actually available

**Problem:** Customers must not reserve unavailable court/time combinations.

**Solution:**

Generate the booking interface directly from the reservation database.

Each slot has a simple state:

**Available / Booked**

Only `Available` slots are selectable. Once a reservation succeeds, that court/time combination immediately becomes `Booked` and disappears or becomes disabled for other customers.

---

### 6. Risk of double booking

**Problem:** Two customers must never hold the same court and time slot.

**Solution:**

Enforce a **database-level unique constraint** on:

**Court + Date + Time Slot**

For example:

`Court 1 + 15 Aug + 7:00 PM`

can exist only once as an active booking.

Even if the frontend makes a mistake, the database refuses a second reservation for the same combination.

---

### 7. Concurrency during booking

**Problem:** Multiple customers may attempt to reserve the same slot simultaneously.

**Solution:**

Do not rely only on the frontend showing the slot as available.

When the customer presses **Confirm Booking**, the backend performs an atomic booking operation:

1. Attempt to create the reservation.
2. Database checks the unique `Court + Date + Time` constraint.
3. First successful request gets the slot.
4. Any simultaneous request that loses the race receives:

**"This slot was just booked. Please choose another available slot."**

This keeps the implementation simple while correctly protecting against concurrent reservations.

---

### 8. Staff verification of bookings

**Problem:** Staff need to determine whether a presented booking is valid.

**Solution:**

Every successful reservation generates:

**QR Code + short booking code**

Example:

`PDL-7F42K`

At the court, staff can either:

- scan the QR code; or
- manually enter `PDL-7F42K`.

The staff page immediately shows:

**VALID BOOKING**

along with the court, time, booker, attendees, and current redemption status.

---

### 9. Preventing repeated use of the same booking

**Problem:** A valid booking must not be redeemed more than once.

**Solution:**

Every reservation contains a simple:

`redeemed = false`

field.

When staff press **Redeem Booking**, the backend atomically changes it to:

`redeemed = true`

The backend only performs the update when the current value is `false`.

Therefore, even if two staff members attempt to redeem the same QR code simultaneously, only one redemption succeeds.

---

### 10. Distinguishing redeemed from unredeemed bookings

**Problem:** Staff need to know whether a booking has already been used.

**Solution:**

The verification page displays a large status immediately after scanning:

**✅ VALID — NOT REDEEMED**

with a **Redeem Booking** button.

After redemption:

**✓ REDEEMED**

**Redeemed at: 8:03 PM**

The Redeem button disappears or becomes disabled.

If someone presents the same pass again, staff immediately see:

**⚠️ ALREADY REDEEMED**

---

## Complete MVP Workflow

**Customer**

`Open booking page`

→ `Choose date`

→ `Choose Court 1 / Court 2`

→ `Choose available slot`

→ `Enter booker + attendees`

→ `Confirm booking`

→ `Database atomically reserves slot`

→ `Receive QR + short code`

**Staff**

`Scan QR / enter code`

→ `System finds booking`

→ `See booking + attendee details`

→ `See VALID / REDEEMED status`

→ `Redeem once`

### Minimal Data Needed

The entire MVP can work with essentially one booking record containing:

`booking_id`

`booking_code`

`court`

`date`

`time_slot`

`booker_name`

`attendee_names`

`redeemed`

`redeemed_at`

plus a database uniqueness rule for:

**`court + date + time_slot`**

This keeps the product small enough for a **4-hour AI-assisted MVP**, while directly addressing every focused problem in the provided list without adding unrelated functionality.