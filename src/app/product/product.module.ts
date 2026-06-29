import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';

import { ProductPageRoutingModule } from './product-routing.module';
import { ProductPage } from './product.page';

@NgModule({
  declarations: [ProductPage],
  imports: [CommonModule, IonicModule, ProductPageRoutingModule],
})
export class ProductPageModule {}
