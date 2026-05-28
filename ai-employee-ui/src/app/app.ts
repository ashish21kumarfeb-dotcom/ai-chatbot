import { Component } from '@angular/core';

import { ChatWidget } from './features/chat/chat-widget/chat-widget';

import { UploadPage } from './features/upload/upload-page/upload-page';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    ChatWidget,
    UploadPage
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
}