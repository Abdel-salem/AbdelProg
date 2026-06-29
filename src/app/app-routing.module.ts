import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  { path: '', redirectTo: 'home', pathMatch: 'full' },
  { path: 'home', loadChildren: () => import('./home/home.module').then((m) => m.HomePageModule) },
  { path: 'cart', loadChildren: () => import('./cart/cart.module').then((m) => m.CartPageModule) },
  {
    path: 'order-summary',
    loadChildren: () => import('./order-summary/order-summary.module').then((m) => m.OrderSummaryPageModule),
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {}
