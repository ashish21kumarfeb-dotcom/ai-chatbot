import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../core/services/api';

@Component({
  selector: 'app-upload-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './upload-page.html',
  styleUrls: ['./upload-page.css']
})
export class UploadPage {

  private api = inject(ApiService);

  uploadedFiles: string[] = [];

 onFileSelected(event: any) {
  const files = event.target.files;

  for (let file of files) {

    // UI update immediately
    this.uploadedFiles = [...this.uploadedFiles, file.name];

    this.api.uploadFile(file).subscribe({
      next: () => console.log('uploaded'),
      error: (err) => console.error(err)
    });
  }

  event.target.value = ''; // IMPORTANT reset input
}

deleteFile(index: number) {

  const file = this.uploadedFiles[index];

  // UI update immediately (no delay)
  this.uploadedFiles =
    this.uploadedFiles.filter((_, i) => i !== index);

  this.api.deleteFile(file).subscribe({
    next: () => console.log('deleted'),
    error: (err) => console.error(err)
  });
}
}