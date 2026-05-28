import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-upload-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './upload-page.html',
  styleUrls: ['./upload-page.css']
})
export class UploadPage {

  uploadedFiles: string[] = [];

  onFileSelected(event: any) {

    const files = event.target.files;

    for (let file of files) {
      this.uploadedFiles.push(file.name);
    }

  }

  deleteFile(index: number) {
    this.uploadedFiles.splice(index, 1);
  }

}