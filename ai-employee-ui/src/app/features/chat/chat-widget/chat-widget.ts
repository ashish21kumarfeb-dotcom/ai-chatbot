import {
  Component,
  signal,
  inject
} from '@angular/core';

import {
  CommonModule
} from '@angular/common';

import {
  FormsModule
} from '@angular/forms';

import {ApiService} from '../../../core/services/api';

@Component({
  selector: 'app-chat-widget',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './chat-widget.html',
  styleUrl: './chat-widget.css'
})
export class ChatWidget{

  private api = inject(ApiService);

  isOpen = signal(false);

  question = '';

  loading = false;

  messages = signal<any[]>([
    {
      sender: 'ai',
      text: 'Hi! I am your AI Employee.'
    }
  ]);

  toggleChat() {

    this.isOpen.update(v => !v);
  }

  sendMessage() {

    if (!this.question.trim()) {
      return;
    }

    const userQuestion = this.question;

    this.messages.update(messages => [
      ...messages,
      {
        sender: 'user',
        text: userQuestion
      }
    ]);

    this.question = '';

    this.loading = true;

    this.api.askQuestion(userQuestion)
      .subscribe({

        next: (response) => {

          this.messages.update(messages => [
            ...messages,
            {
              sender: 'ai',
              text: response.answer
            }
          ]);

          this.loading = false;
        },

        error: () => {

          this.messages.update(messages => [
            ...messages,
            {
              sender: 'ai',
              text: 'Something went wrong.'
            }
          ]);

          this.loading = false;
        }

      });

  }

}