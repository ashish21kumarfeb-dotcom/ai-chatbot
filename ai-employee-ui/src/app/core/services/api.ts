import { Injectable, inject } from '@angular/core';
import {
  HttpClient
} from '@angular/common/http';

import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {ChatResponse} from '../../models/chat-response';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private http = inject(HttpClient);

  private apiUrl = environment.apiUrl;
  private sessionId: string;
  constructor() { 
     const existingSessionId =
      localStorage.getItem('chat_session_id');

    if (existingSessionId) {

      this.sessionId = existingSessionId;

    } else {

      this.sessionId = crypto.randomUUID();

      localStorage.setItem(
        'chat_session_id',
        this.sessionId
      );
    }

    console.log(
      'Session ID:',
      this.sessionId
    );
  }

  getFiles() {
  return this.http.get<any[]>(
    `${this.apiUrl}/upload/files`
  );
}
  askQuestion(question: string,): Observable<ChatResponse> {

    return this.http.post<ChatResponse>(
      `${this.apiUrl}/chat`,
      {
        question,
        session_id: this.sessionId
      }
    );
  }

  uploadFile(file: File): Observable<any> {

    const formData = new FormData();

    formData.append(
      'file',
      file
    );

    return this.http.post(
      `${this.apiUrl}/upload`,
      formData
    );
  }

  deleteFile(filename: string): Observable<any> {

    return this.http.delete(
      `${this.apiUrl}/upload/${filename}`
    );
  }

}