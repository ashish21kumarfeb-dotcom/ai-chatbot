import { ChangeDetectorRef, Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../core/services/api';

@Component({
  selector: 'app-upload-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './upload-page.html',
  styleUrls: ['./upload-page.css']
})
export class UploadPage implements OnInit {

  private api = inject(ApiService);

  uploadedFiles: string[] = [];

  ngOnInit(): void {
    this.loadFiles();
  }
  
constructor(private cdr: ChangeDetectorRef) {}

loadFiles() {
  this.api.getFiles().subscribe({
    next: (files: any[]) => {
      console.log('Before:', this.uploadedFiles);
      this.uploadedFiles = [...files];
      console.log('After:', this.uploadedFiles);
      this.cdr.detectChanges();
    }
  });
}
  onFileSelected(event: Event): void {

    const input = event.target as HTMLInputElement;

    if (!input.files?.length) {
      return;
    }

    Array.from(input.files).forEach((file) => {

      this.api.uploadFile(file).subscribe({
        next: (response: any) => {

          console.log('FILES API RESPONSE', response);

          // If backend returns updated file list
          if (response.files) {
            this.uploadedFiles = response.files;
          } else {
            this.uploadedFiles = [
              ...this.uploadedFiles,
              file.name
            ];
          }
        },
        error: (err) => {
          console.error('Upload failed', err);
        }
      });

    });

    input.value = '';
  }

  deleteFile(index: number): void {

    const file = this.uploadedFiles[index];

    this.uploadedFiles =
      this.uploadedFiles.filter((_, i) => i !== index);

    this.api.deleteFile(file).subscribe({
      next: () => {
        console.log('File deleted');
      },
      error: (err) => {
        console.error('Delete failed', err);

        // Reload if delete failed
        this.loadFiles();
      }
    });
  }
}