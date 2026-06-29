import { Component } from '@angular/core';

@Component({
  selector: 'app-product',
  templateUrl: './product.page.html',
  styleUrls: ['./product.page.scss'],
})
export class ProductPage {
  cartCount = 1;

  product = {
    name: 'EXtreme',
    category: 'Cordless Endomotor',
    tagline: 'Smaller | Lighter | Quieter than ever',
    originalPrice: 12000,
    price: 10000,
    features: [
      'Mini Head for More Comfortable & accessible Experience',
      'Contra-angle rotation 360°',
      'Slim and compact design for maximum comfort and mobility',
      'Miniature contra-angle for better visibility & easier posterior access',
      'Normal head & neck',
    ],
    images: ['assets/products/extreme-1.png', 'assets/products/extreme-2.png', 'assets/products/extreme-3.png'],
  };

  activeImageIndex = 0;
  quantity = 1;
  addedToCart = false;

  selectImage(index: number): void {
    this.activeImageIndex = index;
  }

  increaseQuantity(): void {
    this.quantity++;
  }

  decreaseQuantity(): void {
    if (this.quantity > 1) {
      this.quantity--;
    }
  }

  addToCart(): void {
    this.addedToCart = true;
    this.cartCount += this.quantity;
  }
}
