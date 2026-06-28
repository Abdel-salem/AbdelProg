import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';

import { CartPageRoutingModule } from './cart-routing.module';
import { CartPage } from './cart.page';

@NgModule({
  declarations: [CartPage],
  imports: [CommonModule, IonicModule, CartPageRoutingModule],
})
export class CartPageModule {}
