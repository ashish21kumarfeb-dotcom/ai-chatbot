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

import {
  finalize
} from 'rxjs';

import { ApiService } from '../../../core/services/api';

import {
  ChatMessage
} from '../../../models/chat-message';

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
export class ChatWidget {

  private api = inject(ApiService);

  isOpen = signal(false);

  question = '';

  loading = false;

  messages = signal<ChatMessage[]>([
    {
      sender: 'ai',
      text: 'Hi! I am your AI Employee.'
    }
  ]);

  toggleChat(): void {

    this.isOpen.update(
      value => !value
    );
  }

  private scrollToBottom(): void {

    setTimeout(() => {

      const chatBody =
        document.querySelector(
          '.chat-body'
        );

      if (chatBody) {

        chatBody.scrollTo({
          top: chatBody.scrollHeight,
          behavior: 'smooth'
        });

      }

    }, 0);
  }

  sendMessage(): void {

    if (this.loading) {

      console.warn(
        'Request already in progress'
      );

      return;
    }

    const trimmedQuestion =
      this.question.trim();

    console.log(
      '===================='
    );

    console.log(
      'sendMessage called'
    );

    console.log(
      'Question:',
      trimmedQuestion
    );

    console.log(
      'Session ID:',
      localStorage.getItem(
        'chat_session_id'
      )
    );

    if (!trimmedQuestion) {

      console.warn(
        'Empty question'
      );

      return;
    }

    const userQuestion =
      trimmedQuestion;

    this.messages.update(
      messages => [
        ...messages,
        {
          sender: 'user',
          text: userQuestion
        }
      ]
    );

    this.scrollToBottom();

    this.question = '';

    this.loading = true;

    console.log(
      'Calling API...'
    );

    this.api
      .askQuestion(userQuestion)
      .pipe(

        finalize(() => {

          this.loading = false;

          console.log(
            'Loading set false'
          );

        })

      )
      .subscribe({

        next: response => {

          console.log(
            'API Success'
          );

          console.log(
            response
          );

          const answer =
            response?.answer?.trim()
            || 'No answer received';

          this.messages.update(
            messages => [
              ...messages,
              {
                sender: 'ai',
                text: answer
              }
            ]
          );

          this.scrollToBottom();

        },

        error: err => {

          console.error(
            'API Error'
          );

          console.error(
            err
          );

          this.messages.update(
            messages => [
              ...messages,
              {
                sender: 'ai',
                text:
                  'Something went wrong.'
              }
            ]
          );

          this.scrollToBottom();

        },

        complete: () => {

          console.log(
            'Request completed'
          );

        }

      });

  }

}