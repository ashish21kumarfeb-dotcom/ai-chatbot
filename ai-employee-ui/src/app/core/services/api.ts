import { Injectable, inject } from '@angular/core';
import {
  HttpClient
} from '@angular/common/http';

import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private http = inject(HttpClient);

  private apiUrl = environment.apiUrl;

  askQuestion(question: string): Observable<any> {

    return this.http.post(
      `${this.apiUrl}/chat`,
      {
        question
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