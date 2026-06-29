import { Component } from '@angular/core';

export interface OrderLine {
  name: string;
  quantity: number;
  price: number;
}

export type FulfillmentMethod = 'delivery' | 'pickup';

@Component({
  selector: 'app-order-summary',
  templateUrl: './order-summary.page.html',
  styleUrls: ['./order-summary.page.scss'],
})
export class OrderSummaryPage {
  lines: OrderLine[] = [
    { name: 'EXtreme', quantity: 2, price: 20000 },
    { name: 'Fast Pack Pro', quantity: 1, price: 14000 },
  ];

  fulfillmentMethod: FulfillmentMethod = 'delivery';

  city = '';
  addressLine = '';
  promoCode = '';

  get totalPrice(): number {
    return this.lines.reduce((sum, line) => sum + line.price, 0);
  }

  selectFulfillment(method: FulfillmentMethod): void {
    this.fulfillmentMethod = method;
  }

  selectLocationOnMap(): void {
    // open map picker
  }

  applyPromoCode(): void {
    // validate and apply promo code
  }

  submit(): void {
    // submit order
  }
}
