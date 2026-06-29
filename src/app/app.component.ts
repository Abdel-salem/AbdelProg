import { Component } from '@angular/core';
import { addIcons } from 'ionicons';
import {
  notificationsOutline,
  personCircleOutline,
  walletOutline,
  calendarOutline,
  bagHandleOutline,
  alertCircleOutline,
  informationCircleOutline,
  chevronForwardOutline,
  cubeOutline,
  readerOutline,
  cloudUploadOutline,
  folderOutline,
  documentTextOutline,
  homeOutline,
  bagOutline,
  personOutline,
  cartOutline,
  createOutline,
  trashOutline,
  businessOutline,
  bicycleOutline,
  locationOutline,
  checkmarkDoneOutline,
} from 'ionicons/icons';

addIcons({
  'notifications-outline': notificationsOutline,
  'person-circle-outline': personCircleOutline,
  'wallet-outline': walletOutline,
  'calendar-outline': calendarOutline,
  'bag-handle-outline': bagHandleOutline,
  'alert-circle-outline': alertCircleOutline,
  'information-circle-outline': informationCircleOutline,
  'chevron-forward-outline': chevronForwardOutline,
  'cube-outline': cubeOutline,
  'reader-outline': readerOutline,
  'cloud-upload-outline': cloudUploadOutline,
  'folder-outline': folderOutline,
  'document-text-outline': documentTextOutline,
  'home-outline': homeOutline,
  'bag-outline': bagOutline,
  'person-outline': personOutline,
  'cart-outline': cartOutline,
  'create-outline': createOutline,
  'trash-outline': trashOutline,
  'business-outline': businessOutline,
  'bicycle-outline': bicycleOutline,
  'location-outline': locationOutline,
  'checkmark-done-outline': checkmarkDoneOutline,
});

@Component({
  selector: 'app-root',
  template: '<ion-app><ion-router-outlet></ion-router-outlet></ion-app>',
})
export class AppComponent {}
