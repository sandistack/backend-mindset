# 📁 FILE UPLOAD - Go/Gin (Junior → Senior)

Dokumentasi lengkap tentang file upload di Go dengan Gin framework, dari local storage hingga cloud storage (S3).

---

## 🎯 Kapan Butuh File Upload?

```
Use Cases:
✅ Profile pictures
✅ Document uploads (PDF, contracts)
✅ CSV/Excel imports
✅ Image galleries
✅ Attachments
```

---

## 1️⃣ JUNIOR LEVEL - Basic File Upload

### Single File Upload

```go
// internal/handlers/upload.go
package handlers

import (
    "fmt"
    "net/http"
    "os"
    "path/filepath"
    "github.com/gin-gonic/gin"
    "github.com/google/uuid"
)

type UploadHandler struct {
    uploadDir string
}

func NewUploadHandler(uploadDir string) *UploadHandler {
    // Create upload directory if not exists
    os.MkdirAll(uploadDir, os.ModePerm)
    return &UploadHandler{uploadDir: uploadDir}
}

func (h *UploadHandler) UploadSingle(c *gin.Context) {
    // Get file from form
    file, err := c.FormFile("file")
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{
            "error": "No file provided",
        })
        return
    }

    // Generate unique filename
    ext := filepath.Ext(file.Filename)
    newFilename := fmt.Sprintf("%s%s", uuid.New().String(), ext)
    
    // Save file
    dst := filepath.Join(h.uploadDir, newFilename)
    if err := c.SaveUploadedFile(file, dst); err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{
            "error": "Failed to save file",
        })
        return
    }

    c.JSON(http.StatusOK, gin.H{
        "message":  "File uploaded successfully",
        "filename": newFilename,
        "size":     file.Size,
        "url":      fmt.Sprintf("/uploads/%s", newFilename),
    })
}
```

### Multiple Files Upload

```go
func (h *UploadHandler) UploadMultiple(c *gin.Context) {
    form, err := c.MultipartForm()
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{
            "error": "Invalid form data",
        })
        return
    }

    files := form.File["files"]
    if len(files) == 0 {
        c.JSON(http.StatusBadRequest, gin.H{
            "error": "No files provided",
        })
        return
    }

    var uploaded []map[string]interface{}

    for _, file := range files {
        ext := filepath.Ext(file.Filename)
        newFilename := fmt.Sprintf("%s%s", uuid.New().String(), ext)
        dst := filepath.Join(h.uploadDir, newFilename)

        if err := c.SaveUploadedFile(file, dst); err != nil {
            continue // Skip failed files
        }

        uploaded = append(uploaded, map[string]interface{}{
            "original_name": file.Filename,
            "filename":      newFilename,
            "size":          file.Size,
            "url":           fmt.Sprintf("/uploads/%s", newFilename),
        })
    }

    c.JSON(http.StatusOK, gin.H{
        "message": fmt.Sprintf("%d files uploaded", len(uploaded)),
        "files":   uploaded,
    })
}
```

### Router Setup

```go
// cmd/api/main.go
package main

import (
    "github.com/gin-gonic/gin"
    "myapp/internal/handlers"
)

func main() {
    r := gin.Default()

    // Serve static files
    r.Static("/uploads", "./uploads")

    // Set max upload size (8 MB)
    r.MaxMultipartMemory = 8 << 20

    uploadHandler := handlers.NewUploadHandler("./uploads")

    api := r.Group("/api")
    {
        api.POST("/upload", uploadHandler.UploadSingle)
        api.POST("/upload/multiple", uploadHandler.UploadMultiple)
    }

    r.Run(":8080")
}
```

---

## 2️⃣ MID LEVEL - File Validation

### Validation Service

```go
// internal/services/file_validator.go
package services

import (
    "errors"
    "mime/multipart"
    "net/http"
    "path/filepath"
    "strings"
)

type FileValidator struct {
    MaxSize           int64
    AllowedExtensions []string
    AllowedMimeTypes  []string
}

func NewImageValidator() *FileValidator {
    return &FileValidator{
        MaxSize:           5 * 1024 * 1024, // 5 MB
        AllowedExtensions: []string{".jpg", ".jpeg", ".png", ".gif", ".webp"},
        AllowedMimeTypes:  []string{"image/jpeg", "image/png", "image/gif", "image/webp"},
    }
}

func NewDocumentValidator() *FileValidator {
    return &FileValidator{
        MaxSize:           10 * 1024 * 1024, // 10 MB
        AllowedExtensions: []string{".pdf", ".doc", ".docx", ".xls", ".xlsx"},
        AllowedMimeTypes: []string{
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        },
    }
}

func (v *FileValidator) Validate(file *multipart.FileHeader) error {
    // Check file size
    if file.Size > v.MaxSize {
        return errors.New("file size exceeds limit")
    }

    // Check extension
    ext := strings.ToLower(filepath.Ext(file.Filename))
    if !v.isAllowedExtension(ext) {
        return errors.New("file extension not allowed")
    }

    // Check MIME type (read first 512 bytes)
    f, err := file.Open()
    if err != nil {
        return errors.New("failed to open file")
    }
    defer f.Close()

    buffer := make([]byte, 512)
    _, err = f.Read(buffer)
    if err != nil {
        return errors.New("failed to read file")
    }

    mimeType := http.DetectContentType(buffer)
    if !v.isAllowedMimeType(mimeType) {
        return errors.New("file type not allowed")
    }

    return nil
}

func (v *FileValidator) isAllowedExtension(ext string) bool {
    for _, allowed := range v.AllowedExtensions {
        if ext == allowed {
            return true
        }
    }
    return false
}

func (v *FileValidator) isAllowedMimeType(mimeType string) bool {
    for _, allowed := range v.AllowedMimeTypes {
        if strings.HasPrefix(mimeType, allowed) {
            return true
        }
    }
    return false
}
```

### Upload Handler dengan Validation

```go
// internal/handlers/upload.go
func (h *UploadHandler) UploadAvatar(c *gin.Context) {
    file, err := c.FormFile("avatar")
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "No file provided"})
        return
    }

    // Validate
    validator := services.NewImageValidator()
    if err := validator.Validate(file); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    // Get user ID from context (set by auth middleware)
    userID := c.GetUint("user_id")

    // Generate filename
    ext := filepath.Ext(file.Filename)
    filename := fmt.Sprintf("avatar_%d%s", userID, ext)
    dst := filepath.Join(h.uploadDir, "avatars", filename)

    // Ensure directory exists
    os.MkdirAll(filepath.Dir(dst), os.ModePerm)

    // Save file
    if err := c.SaveUploadedFile(file, dst); err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save file"})
        return
    }

    // Update user profile in database
    // h.userRepo.UpdateAvatar(userID, filename)

    c.JSON(http.StatusOK, gin.H{
        "message": "Avatar uploaded successfully",
        "url":     fmt.Sprintf("/uploads/avatars/%s", filename),
    })
}
```

---

## 3️⃣ MID-SENIOR LEVEL - Image Processing

### Install Dependencies

```bash
go get github.com/disintegration/imaging
```

### Image Service

```go
// internal/services/image_service.go
package services

import (
    "fmt"
    "image"
    "os"
    "path/filepath"
    
    "github.com/disintegration/imaging"
)

type ImageService struct {
    uploadDir string
}

func NewImageService(uploadDir string) *ImageService {
    return &ImageService{uploadDir: uploadDir}
}

type ResizeOptions struct {
    Width   int
    Height  int
    Quality int
}

func (s *ImageService) ResizeImage(srcPath string, opts ResizeOptions) (string, error) {
    // Open source image
    src, err := imaging.Open(srcPath)
    if err != nil {
        return "", fmt.Errorf("failed to open image: %w", err)
    }

    // Resize (maintain aspect ratio)
    resized := imaging.Fit(src, opts.Width, opts.Height, imaging.Lanczos)

    // Generate output path
    ext := filepath.Ext(srcPath)
    base := srcPath[:len(srcPath)-len(ext)]
    dstPath := fmt.Sprintf("%s_%dx%d%s", base, opts.Width, opts.Height, ext)

    // Save with quality
    err = imaging.Save(resized, dstPath, imaging.JPEGQuality(opts.Quality))
    if err != nil {
        return "", fmt.Errorf("failed to save image: %w", err)
    }

    return dstPath, nil
}

func (s *ImageService) CreateThumbnail(srcPath string, size int) (string, error) {
    src, err := imaging.Open(srcPath)
    if err != nil {
        return "", err
    }

    // Create square thumbnail
    thumb := imaging.Thumbnail(src, size, size, imaging.Lanczos)

    ext := filepath.Ext(srcPath)
    base := srcPath[:len(srcPath)-len(ext)]
    thumbPath := fmt.Sprintf("%s_thumb%s", base, ext)

    err = imaging.Save(thumb, thumbPath, imaging.JPEGQuality(85))
    if err != nil {
        return "", err
    }

    return thumbPath, nil
}

func (s *ImageService) ProcessUpload(srcPath string) (*ProcessedImage, error) {
    result := &ProcessedImage{Original: srcPath}

    // Create medium size (800x800)
    medium, err := s.ResizeImage(srcPath, ResizeOptions{
        Width:   800,
        Height:  800,
        Quality: 85,
    })
    if err == nil {
        result.Medium = medium
    }

    // Create thumbnail (150x150)
    thumb, err := s.CreateThumbnail(srcPath, 150)
    if err == nil {
        result.Thumbnail = thumb
    }

    return result, nil
}

type ProcessedImage struct {
    Original  string `json:"original"`
    Medium    string `json:"medium"`
    Thumbnail string `json:"thumbnail"`
}
```

### Async Image Processing dengan Goroutines

```go
// internal/handlers/upload.go
func (h *UploadHandler) UploadWithProcessing(c *gin.Context) {
    file, err := c.FormFile("file")
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "No file provided"})
        return
    }

    // Validate
    validator := services.NewImageValidator()
    if err := validator.Validate(file); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    // Save original
    ext := filepath.Ext(file.Filename)
    filename := fmt.Sprintf("%s%s", uuid.New().String(), ext)
    dst := filepath.Join(h.uploadDir, filename)

    if err := c.SaveUploadedFile(file, dst); err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save file"})
        return
    }

    // Process in background
    go func(filePath string) {
        imageService := services.NewImageService(h.uploadDir)
        result, err := imageService.ProcessUpload(filePath)
        if err != nil {
            log.Printf("Image processing failed: %v", err)
            return
        }
        log.Printf("Image processed: %+v", result)
        
        // Update database with processed paths
        // h.fileRepo.UpdateProcessedPaths(...)
    }(dst)

    c.JSON(http.StatusOK, gin.H{
        "message":  "File uploaded, processing in background",
        "filename": filename,
        "url":      fmt.Sprintf("/uploads/%s", filename),
    })
}
```

---

## 4️⃣ SENIOR LEVEL - AWS S3 Storage

### Install AWS SDK

```bash
go get github.com/aws/aws-sdk-go-v2
go get github.com/aws/aws-sdk-go-v2/config
go get github.com/aws/aws-sdk-go-v2/service/s3
go get github.com/aws/aws-sdk-go-v2/feature/s3/manager
```

### S3 Service

```go
// internal/services/s3_service.go
package services

import (
    "context"
    "fmt"
    "mime/multipart"
    "path/filepath"
    "time"

    "github.com/aws/aws-sdk-go-v2/aws"
    "github.com/aws/aws-sdk-go-v2/config"
    "github.com/aws/aws-sdk-go-v2/feature/s3/manager"
    "github.com/aws/aws-sdk-go-v2/service/s3"
    "github.com/google/uuid"
)

type S3Service struct {
    client     *s3.Client
    uploader   *manager.Uploader
    bucket     string
    region     string
    baseURL    string
}

func NewS3Service(bucket, region string) (*S3Service, error) {
    cfg, err := config.LoadDefaultConfig(context.TODO(),
        config.WithRegion(region),
    )
    if err != nil {
        return nil, fmt.Errorf("failed to load AWS config: %w", err)
    }

    client := s3.NewFromConfig(cfg)
    uploader := manager.NewUploader(client)

    return &S3Service{
        client:   client,
        uploader: uploader,
        bucket:   bucket,
        region:   region,
        baseURL:  fmt.Sprintf("https://%s.s3.%s.amazonaws.com", bucket, region),
    }, nil
}

type UploadResult struct {
    Key      string `json:"key"`
    URL      string `json:"url"`
    Size     int64  `json:"size"`
    MimeType string `json:"mime_type"`
}

func (s *S3Service) Upload(ctx context.Context, file *multipart.FileHeader, folder string) (*UploadResult, error) {
    // Open file
    src, err := file.Open()
    if err != nil {
        return nil, fmt.Errorf("failed to open file: %w", err)
    }
    defer src.Close()

    // Generate unique key
    ext := filepath.Ext(file.Filename)
    key := fmt.Sprintf("%s/%s%s", folder, uuid.New().String(), ext)

    // Detect content type
    buffer := make([]byte, 512)
    src.Read(buffer)
    contentType := http.DetectContentType(buffer)
    src.Seek(0, 0) // Reset reader

    // Upload to S3
    result, err := s.uploader.Upload(ctx, &s3.PutObjectInput{
        Bucket:      aws.String(s.bucket),
        Key:         aws.String(key),
        Body:        src,
        ContentType: aws.String(contentType),
    })
    if err != nil {
        return nil, fmt.Errorf("failed to upload to S3: %w", err)
    }

    return &UploadResult{
        Key:      key,
        URL:      result.Location,
        Size:     file.Size,
        MimeType: contentType,
    }, nil
}

func (s *S3Service) GeneratePresignedURL(ctx context.Context, key string, expiration time.Duration) (string, error) {
    presignClient := s3.NewPresignClient(s.client)

    request, err := presignClient.PresignGetObject(ctx, &s3.GetObjectInput{
        Bucket: aws.String(s.bucket),
        Key:    aws.String(key),
    }, s3.WithPresignExpires(expiration))
    if err != nil {
        return "", fmt.Errorf("failed to generate presigned URL: %w", err)
    }

    return request.URL, nil
}

func (s *S3Service) GeneratePresignedUploadURL(ctx context.Context, key string, contentType string, expiration time.Duration) (string, error) {
    presignClient := s3.NewPresignClient(s.client)

    request, err := presignClient.PresignPutObject(ctx, &s3.PutObjectInput{
        Bucket:      aws.String(s.bucket),
        Key:         aws.String(key),
        ContentType: aws.String(contentType),
    }, s3.WithPresignExpires(expiration))
    if err != nil {
        return "", fmt.Errorf("failed to generate presigned upload URL: %w", err)
    }

    return request.URL, nil
}

func (s *S3Service) Delete(ctx context.Context, key string) error {
    _, err := s.client.DeleteObject(ctx, &s3.DeleteObjectInput{
        Bucket: aws.String(s.bucket),
        Key:    aws.String(key),
    })
    return err
}
```

### S3 Upload Handler

```go
// internal/handlers/upload.go
func (h *UploadHandler) UploadToS3(c *gin.Context) {
    file, err := c.FormFile("file")
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "No file provided"})
        return
    }

    // Validate
    validator := services.NewImageValidator()
    if err := validator.Validate(file); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    // Upload to S3
    s3Service, _ := services.NewS3Service(
        os.Getenv("AWS_BUCKET"),
        os.Getenv("AWS_REGION"),
    )

    result, err := s3Service.Upload(c.Request.Context(), file, "uploads")
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Upload failed"})
        return
    }

    c.JSON(http.StatusOK, gin.H{
        "message": "File uploaded to S3",
        "key":     result.Key,
        "url":     result.URL,
        "size":    result.Size,
    })
}

// Generate presigned URL for direct frontend upload
func (h *UploadHandler) GetPresignedUploadURL(c *gin.Context) {
    filename := c.Query("filename")
    contentType := c.Query("content_type")

    if filename == "" || contentType == "" {
        c.JSON(http.StatusBadRequest, gin.H{"error": "filename and content_type required"})
        return
    }

    ext := filepath.Ext(filename)
    key := fmt.Sprintf("uploads/%s%s", uuid.New().String(), ext)

    s3Service, _ := services.NewS3Service(
        os.Getenv("AWS_BUCKET"),
        os.Getenv("AWS_REGION"),
    )

    url, err := s3Service.GeneratePresignedUploadURL(
        c.Request.Context(),
        key,
        contentType,
        15*time.Minute,
    )
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate URL"})
        return
    }

    c.JSON(http.StatusOK, gin.H{
        "upload_url": url,
        "key":        key,
        "expires_in": "15 minutes",
    })
}
```

---

## 5️⃣ EXPERT LEVEL - Chunked Upload untuk Large Files

### Chunked Upload Handler

```go
// internal/handlers/chunked_upload.go
package handlers

import (
    "fmt"
    "io"
    "net/http"
    "os"
    "path/filepath"
    "sync"

    "github.com/gin-gonic/gin"
)

type ChunkedUploadHandler struct {
    uploadDir string
    sessions  map[string]*UploadSession
    mu        sync.RWMutex
}

type UploadSession struct {
    ID          string
    Filename    string
    TotalChunks int
    Received    map[int]bool
    TempDir     string
}

func NewChunkedUploadHandler(uploadDir string) *ChunkedUploadHandler {
    return &ChunkedUploadHandler{
        uploadDir: uploadDir,
        sessions:  make(map[string]*UploadSession),
    }
}

// Initialize upload session
func (h *ChunkedUploadHandler) InitUpload(c *gin.Context) {
    var req struct {
        Filename    string `json:"filename" binding:"required"`
        TotalChunks int    `json:"total_chunks" binding:"required"`
    }

    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    sessionID := uuid.New().String()
    tempDir := filepath.Join(h.uploadDir, "temp", sessionID)
    os.MkdirAll(tempDir, os.ModePerm)

    session := &UploadSession{
        ID:          sessionID,
        Filename:    req.Filename,
        TotalChunks: req.TotalChunks,
        Received:    make(map[int]bool),
        TempDir:     tempDir,
    }

    h.mu.Lock()
    h.sessions[sessionID] = session
    h.mu.Unlock()

    c.JSON(http.StatusOK, gin.H{
        "session_id":   sessionID,
        "total_chunks": req.TotalChunks,
    })
}

// Upload single chunk
func (h *ChunkedUploadHandler) UploadChunk(c *gin.Context) {
    sessionID := c.PostForm("session_id")
    chunkIndex := c.PostForm("chunk_index")

    h.mu.RLock()
    session, exists := h.sessions[sessionID]
    h.mu.RUnlock()

    if !exists {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid session"})
        return
    }

    file, err := c.FormFile("chunk")
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "No chunk provided"})
        return
    }

    // Save chunk
    chunkPath := filepath.Join(session.TempDir, fmt.Sprintf("chunk_%s", chunkIndex))
    if err := c.SaveUploadedFile(file, chunkPath); err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save chunk"})
        return
    }

    // Mark chunk as received
    idx, _ := strconv.Atoi(chunkIndex)
    h.mu.Lock()
    session.Received[idx] = true
    receivedCount := len(session.Received)
    h.mu.Unlock()

    c.JSON(http.StatusOK, gin.H{
        "message":        "Chunk uploaded",
        "chunk_index":    idx,
        "received_count": receivedCount,
        "total_chunks":   session.TotalChunks,
    })
}

// Complete upload - merge chunks
func (h *ChunkedUploadHandler) CompleteUpload(c *gin.Context) {
    var req struct {
        SessionID string `json:"session_id" binding:"required"`
    }

    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    h.mu.RLock()
    session, exists := h.sessions[req.SessionID]
    h.mu.RUnlock()

    if !exists {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid session"})
        return
    }

    // Check all chunks received
    if len(session.Received) != session.TotalChunks {
        c.JSON(http.StatusBadRequest, gin.H{
            "error":    "Missing chunks",
            "received": len(session.Received),
            "expected": session.TotalChunks,
        })
        return
    }

    // Merge chunks
    ext := filepath.Ext(session.Filename)
    finalFilename := fmt.Sprintf("%s%s", uuid.New().String(), ext)
    finalPath := filepath.Join(h.uploadDir, finalFilename)

    finalFile, err := os.Create(finalPath)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create file"})
        return
    }
    defer finalFile.Close()

    for i := 0; i < session.TotalChunks; i++ {
        chunkPath := filepath.Join(session.TempDir, fmt.Sprintf("chunk_%d", i))
        chunkData, err := os.ReadFile(chunkPath)
        if err != nil {
            c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to read chunk"})
            return
        }
        finalFile.Write(chunkData)
    }

    // Cleanup temp files
    os.RemoveAll(session.TempDir)

    h.mu.Lock()
    delete(h.sessions, req.SessionID)
    h.mu.Unlock()

    c.JSON(http.StatusOK, gin.H{
        "message":  "Upload complete",
        "filename": finalFilename,
        "url":      fmt.Sprintf("/uploads/%s", finalFilename),
    })
}
```

---

## 📋 Quick Reference

### File Upload Checklist

```
□ Validate file extension
□ Validate file size
□ Validate MIME type (read file content)
□ Generate unique filename
□ Store securely
□ Process images in goroutines
□ Use presigned URLs for private files
□ Cleanup temp files
□ Log all upload activities
```

### Common Content Types

```go
var ImageMimeTypes = map[string][]string{
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png":  {".png"},
    "image/gif":  {".gif"},
    "image/webp": {".webp"},
}

var DocumentMimeTypes = map[string][]string{
    "application/pdf": {".pdf"},
    "application/msword": {".doc"},
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {".docx"},
}
```

---

## 🔗 Related Docs

- [CONCURRENCY.md](CONCURRENCY.md) - Async image processing
- [SECURITY.md](../03-authentication/SECURITY.md) - File upload security
