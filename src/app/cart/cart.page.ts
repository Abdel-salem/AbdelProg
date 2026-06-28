import { Component } from '@angular/core';

export interface CartItem {
  id: string;
  name: string;
  category: string;
  price: number;
  quantity: number;
  image: string;
}

@Component({
  selector: 'app-cart',
  templateUrl: './cart.page.html',
  styleUrls: ['./cart.page.scss'],
})
export class CartPage {
  notificationCount = 2;

  items: CartItem[] = [
    {
      id: '1',
      name: 'EXtreme',
      category: 'Endomotor',
      price: 10000,
      quantity: 1,
      image: 'assets/products/extreme.png',
    },
    {
      id: '2',
      name: 'Fast Pack Pro',
      category: 'Obturation System',
      price: 14000,
      quantity: 1,
      image: 'assets/products/fast-pack-pro.png',
    },
  ];

  get total(): number {
    return this.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  }

  editItem(item: CartItem): void {
    // open edit quantity flow
  }

  removeItem(item: CartItem): void {
    this.items = this.items.filter((i) => i.id !== item.id);
  }

  checkout(): void {
    // navigate to checkout flow
  }
}
