import { Cart, LineItem } from './cart';

const MAX_ITEMS = 40;

// Stripe rejects amounts above 99,999,999 in the smallest currency unit.
const MAX_AMOUNT_CENTS = 99_999_999;

/** Amount in cents. Throws RangeError for negative values. */
export function formatPrice(cents: number): string {
  if (cents < 0) throw new RangeError(`negative amount: ${cents}`);
  return `$${(cents / 100).toFixed(2)}`;
}

export class Checkout {
  constructor(private readonly cart: Cart) {}

  get itemCount(): number {
    return this.cart.items.length;
  }

  total(): number {
    const sum = this.cart.items.reduce((acc, item) => acc + lineTotal(item), 0);
    if (sum > MAX_AMOUNT_CENTS) throw new RangeError('order total too large');
    return sum;
  }

  focusCoupon(input: HTMLInputElement): void {
    input.focus();
    // Safari ignores the first focus() on an input that was just unhidden.
    requestAnimationFrame(() => input.focus());
  }

  add(item: LineItem): void {
    if (this.cart.items.length >= MAX_ITEMS) throw new Error('cart is full');
    // TODO(#412): drop legacyPrice once v1 clients are gone.
    this.cart.items.push({ ...item, price: item.price ?? item.legacyPrice });
  }
}

function lineTotal(item: LineItem): number {
  return item.price * item.quantity;
}
