import { Component } from '@angular/core';

export interface OrderInstallment {
  paid: number;
  total: number;
}

export interface Order {
  id: string;
  status: 'Active' | 'Completed' | 'Overdue';
  installmentsPlanLabel: string;
  totalAmount: number;
  paidAmount: number;
  remainingAmount: number;
  installments: OrderInstallment;
  nextDueAmount: number;
  nextDueDate: string;
}

@Component({
  selector: 'app-home',
  templateUrl: './home.page.html',
  styleUrls: ['./home.page.scss'],
})
export class HomePage {
  userName = 'John Doe';
  notificationCount = 3;

  summary = {
    totalOutstanding: 17500,
    totalOutstandingOrders: 2,
    nextPaymentAmount: 1750,
    nextPaymentDueInDays: 5,
    nextPaymentDate: '12 Jun 2025',
    activeOrders: 2,
    overdueCount: 0,
  };

  showReminder = true;

  reminder = {
    orderId: 'ORD-2025-001234',
    installmentNumber: 4,
    totalInstallments: 6,
    dueDate: '12 Jun 2025',
  };

  orders: Order[] = [
    {
      id: 'ORD-2025-001234',
      status: 'Active',
      installmentsPlanLabel: '6 Installments Plan',
      totalAmount: 10500,
      paidAmount: 5250,
      remainingAmount: 5250,
      installments: { paid: 3, total: 6 },
      nextDueAmount: 1750,
      nextDueDate: '12 Jun 2025',
    },
    {
      id: 'ORD-2025-001235',
      status: 'Active',
      installmentsPlanLabel: '12 Installments Plan',
      totalAmount: 12000,
      paidAmount: 2250,
      remainingAmount: 9750,
      installments: { paid: 1, total: 12 },
      nextDueAmount: 750,
      nextDueDate: '28 Jun 2025',
    },
  ];

  installmentProgress(order: Order): number {
    return order.installments.total === 0
      ? 0
      : order.installments.paid / order.installments.total;
  }

  viewAllOrders(): void {
    // navigate to orders list
  }

  viewOrderDetails(order: Order): void {
    // navigate to order detail page
  }

  uploadReceipt(order: Order): void {
    // open receipt upload flow
  }

  viewDocuments(order: Order): void {
    // navigate to order documents
  }

  exploreMarketplace(): void {
    // navigate to marketplace
  }

  dismissReminder(): void {
    this.showReminder = false;
  }
}
