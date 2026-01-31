# 📁 FILE UPLOAD - Express.js (Junior → Senior)

Dokumentasi lengkap tentang file upload di Express dengan Multer, dari local storage hingga cloud storage (S3).

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

## 1️⃣ JUNIOR LEVEL - Basic File Upload dengan Multer

### Install Dependencies

```bash
npm install multer uuid
```

### Basic Multer Setup

```javascript
// src/middleware/upload.js
const multer = require('multer');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

// Storage configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    const filename = `${uuidv4()}${ext}`;
    cb(null, filename);
  }
});

// Basic upload middleware
const upload = multer({
  storage,
  limits: {
    fileSize: 5 * 1024 * 1024 // 5 MB
  }
});

module.exports = upload;
```

### Upload Routes

```javascript
// src/routes/upload.routes.js
const express = require('express');
const router = express.Router();
const upload = require('../middleware/upload');
const { authMiddleware } = require('../middleware/auth');

// Single file upload
router.post('/single', authMiddleware, upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file provided' });
  }

  res.json({
    message: 'File uploaded successfully',
    file: {
      filename: req.file.filename,
      originalname: req.file.originalname,
      size: req.file.size,
      mimetype: req.file.mimetype,
      url: `/uploads/${req.file.filename}`
    }
  });
});

// Multiple files upload
router.post('/multiple', authMiddleware, upload.array('files', 10), (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({ error: 'No files provided' });
  }

  const files = req.files.map(file => ({
    filename: file.filename,
    originalname: file.originalname,
    size: file.size,
    mimetype: file.mimetype,
    url: `/uploads/${file.filename}`
  }));

  res.json({
    message: `${files.length} files uploaded`,
    files
  });
});

module.exports = router;
```

### Serve Static Files

```javascript
// src/app.js
const express = require('express');
const path = require('path');

const app = express();

// Serve uploaded files
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

// Routes
app.use('/api/upload', require('./routes/upload.routes'));

module.exports = app;
```

---

## 2️⃣ MID LEVEL - File Validation

### Advanced Multer Configuration

```javascript
// src/middleware/upload.js
const multer = require('multer');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

// Allowed file types
const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
const DOCUMENT_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
];

// File filter
const fileFilter = (allowedTypes) => (req, file, cb) => {
  if (allowedTypes.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(new Error(`Invalid file type. Allowed: ${allowedTypes.join(', ')}`), false);
  }
};

// Storage configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    let folder = 'uploads/misc';
    
    if (IMAGE_TYPES.includes(file.mimetype)) {
      folder = 'uploads/images';
    } else if (DOCUMENT_TYPES.includes(file.mimetype)) {
      folder = 'uploads/documents';
    }
    
    // Create folder if not exists
    const fs = require('fs');
    fs.mkdirSync(folder, { recursive: true });
    
    cb(null, folder);
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    const filename = `${Date.now()}-${uuidv4()}${ext}`;
    cb(null, filename);
  }
});

// Image upload
const uploadImage = multer({
  storage,
  limits: { fileSize: 5 * 1024 * 1024 }, // 5 MB
  fileFilter: fileFilter(IMAGE_TYPES)
});

// Document upload
const uploadDocument = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10 MB
  fileFilter: fileFilter(DOCUMENT_TYPES)
});

// General upload
const uploadAny = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: fileFilter([...IMAGE_TYPES, ...DOCUMENT_TYPES])
});

module.exports = {
  uploadImage,
  uploadDocument,
  uploadAny
};
```

### Error Handler

```javascript
// src/middleware/uploadError.js
const multer = require('multer');

const uploadErrorHandler = (err, req, res, next) => {
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        error: 'File too large',
        message: 'Maximum file size exceeded'
      });
    }
    if (err.code === 'LIMIT_FILE_COUNT') {
      return res.status(400).json({
        error: 'Too many files',
        message: 'Maximum number of files exceeded'
      });
    }
    return res.status(400).json({
      error: 'Upload error',
      message: err.message
    });
  }
  
  if (err.message.includes('Invalid file type')) {
    return res.status(400).json({
      error: 'Invalid file type',
      message: err.message
    });
  }
  
  next(err);
};

module.exports = uploadErrorHandler;
```

### File Validation Service

```javascript
// src/services/fileValidator.service.js
const fs = require('fs').promises;
const path = require('path');
const fileType = require('file-type');

class FileValidatorService {
  constructor() {
    this.imageTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    this.documentTypes = ['application/pdf'];
  }

  async validateImage(filePath, maxSizeMB = 5) {
    const errors = [];

    // Check file exists
    try {
      await fs.access(filePath);
    } catch {
      return { valid: false, errors: ['File not found'] };
    }

    // Check file size
    const stats = await fs.stat(filePath);
    const maxSize = maxSizeMB * 1024 * 1024;
    if (stats.size > maxSize) {
      errors.push(`File size exceeds ${maxSizeMB}MB limit`);
    }

    // Check actual file type (not just extension)
    const buffer = await fs.readFile(filePath);
    const type = await fileType.fromBuffer(buffer);
    
    if (!type || !this.imageTypes.includes(type.mime)) {
      errors.push('Invalid image file');
    }

    return {
      valid: errors.length === 0,
      errors,
      type: type?.mime
    };
  }

  async validateDocument(filePath, maxSizeMB = 10) {
    const errors = [];

    try {
      await fs.access(filePath);
    } catch {
      return { valid: false, errors: ['File not found'] };
    }

    const stats = await fs.stat(filePath);
    const maxSize = maxSizeMB * 1024 * 1024;
    if (stats.size > maxSize) {
      errors.push(`File size exceeds ${maxSizeMB}MB limit`);
    }

    const ext = path.extname(filePath).toLowerCase();
    const allowedExts = ['.pdf', '.doc', '.docx', '.xls', '.xlsx'];
    if (!allowedExts.includes(ext)) {
      errors.push('Invalid document type');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }
}

module.exports = new FileValidatorService();
```

---

## 3️⃣ MID-SENIOR LEVEL - Image Processing

### Install Sharp

```bash
npm install sharp
```

### Image Service

```javascript
// src/services/image.service.js
const sharp = require('sharp');
const path = require('path');
const fs = require('fs').promises;

class ImageService {
  constructor(uploadDir = 'uploads') {
    this.uploadDir = uploadDir;
  }

  async resize(inputPath, options = {}) {
    const {
      width = 800,
      height = 800,
      fit = 'inside',
      quality = 85
    } = options;

    const ext = path.extname(inputPath);
    const base = inputPath.slice(0, -ext.length);
    const outputPath = `${base}_${width}x${height}${ext}`;

    await sharp(inputPath)
      .resize(width, height, { fit, withoutEnlargement: true })
      .jpeg({ quality })
      .toFile(outputPath);

    return outputPath;
  }

  async createThumbnail(inputPath, size = 150) {
    const ext = path.extname(inputPath);
    const base = inputPath.slice(0, -ext.length);
    const thumbPath = `${base}_thumb${ext}`;

    await sharp(inputPath)
      .resize(size, size, { fit: 'cover' })
      .jpeg({ quality: 80 })
      .toFile(thumbPath);

    return thumbPath;
  }

  async processUpload(inputPath) {
    const results = {
      original: inputPath,
      medium: null,
      thumbnail: null
    };

    try {
      // Create medium size
      results.medium = await this.resize(inputPath, {
        width: 800,
        height: 800
      });

      // Create thumbnail
      results.thumbnail = await this.createThumbnail(inputPath, 150);
    } catch (error) {
      console.error('Image processing error:', error);
    }

    return results;
  }

  async convertToWebP(inputPath) {
    const ext = path.extname(inputPath);
    const webpPath = inputPath.replace(ext, '.webp');

    await sharp(inputPath)
      .webp({ quality: 85 })
      .toFile(webpPath);

    return webpPath;
  }

  async getMetadata(inputPath) {
    const metadata = await sharp(inputPath).metadata();
    return {
      width: metadata.width,
      height: metadata.height,
      format: metadata.format,
      size: metadata.size
    };
  }
}

module.exports = new ImageService();
```

### Upload dengan Image Processing

```javascript
// src/routes/upload.routes.js
const express = require('express');
const router = express.Router();
const { uploadImage } = require('../middleware/upload');
const imageService = require('../services/image.service');
const { authMiddleware } = require('../middleware/auth');

router.post('/avatar', authMiddleware, uploadImage.single('avatar'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file provided' });
    }

    // Process image
    const processed = await imageService.processUpload(req.file.path);

    // Update user avatar in database
    // await prisma.user.update({
    //   where: { id: req.user.id },
    //   data: { avatar: processed.thumbnail }
    // });

    res.json({
      message: 'Avatar uploaded and processed',
      images: {
        original: `/${processed.original}`,
        medium: `/${processed.medium}`,
        thumbnail: `/${processed.thumbnail}`
      }
    });
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: 'Failed to process image' });
  }
});

module.exports = router;
```

---

## 4️⃣ SENIOR LEVEL - AWS S3 Storage

### Install AWS SDK

```bash
npm install @aws-sdk/client-s3 @aws-sdk/s3-request-presigner multer-s3
```

### S3 Service

```javascript
// src/services/s3.service.js
const {
  S3Client,
  PutObjectCommand,
  GetObjectCommand,
  DeleteObjectCommand
} = require('@aws-sdk/client-s3');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');
const { v4: uuidv4 } = require('uuid');
const path = require('path');

class S3Service {
  constructor() {
    this.client = new S3Client({
      region: process.env.AWS_REGION,
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
      }
    });
    this.bucket = process.env.AWS_BUCKET;
  }

  async upload(file, folder = 'uploads') {
    const ext = path.extname(file.originalname);
    const key = `${folder}/${uuidv4()}${ext}`;

    const command = new PutObjectCommand({
      Bucket: this.bucket,
      Key: key,
      Body: file.buffer,
      ContentType: file.mimetype,
      ACL: 'private'
    });

    await this.client.send(command);

    return {
      key,
      url: `https://${this.bucket}.s3.${process.env.AWS_REGION}.amazonaws.com/${key}`,
      size: file.size,
      mimetype: file.mimetype
    };
  }

  async getSignedDownloadUrl(key, expiresIn = 3600) {
    const command = new GetObjectCommand({
      Bucket: this.bucket,
      Key: key
    });

    return getSignedUrl(this.client, command, { expiresIn });
  }

  async getSignedUploadUrl(key, contentType, expiresIn = 3600) {
    const command = new PutObjectCommand({
      Bucket: this.bucket,
      Key: key,
      ContentType: contentType
    });

    return getSignedUrl(this.client, command, { expiresIn });
  }

  async delete(key) {
    const command = new DeleteObjectCommand({
      Bucket: this.bucket,
      Key: key
    });

    await this.client.send(command);
    return true;
  }
}

module.exports = new S3Service();
```

### Multer S3 Storage

```javascript
// src/middleware/s3Upload.js
const multer = require('multer');
const multerS3 = require('multer-s3');
const { S3Client } = require('@aws-sdk/client-s3');
const { v4: uuidv4 } = require('uuid');
const path = require('path');

const s3Client = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
  }
});

const s3Upload = multer({
  storage: multerS3({
    s3: s3Client,
    bucket: process.env.AWS_BUCKET,
    acl: 'private',
    contentType: multerS3.AUTO_CONTENT_TYPE,
    key: (req, file, cb) => {
      const ext = path.extname(file.originalname);
      const key = `uploads/${Date.now()}-${uuidv4()}${ext}`;
      cb(null, key);
    }
  }),
  limits: {
    fileSize: 10 * 1024 * 1024 // 10 MB
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = [
      'image/jpeg', 'image/png', 'image/gif',
      'application/pdf'
    ];
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type'), false);
    }
  }
});

module.exports = s3Upload;
```

### S3 Upload Routes

```javascript
// src/routes/upload.routes.js
const express = require('express');
const router = express.Router();
const s3Upload = require('../middleware/s3Upload');
const s3Service = require('../services/s3.service');
const { authMiddleware } = require('../middleware/auth');

// Direct upload to S3
router.post('/s3', authMiddleware, s3Upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file provided' });
  }

  res.json({
    message: 'File uploaded to S3',
    file: {
      key: req.file.key,
      location: req.file.location,
      size: req.file.size,
      mimetype: req.file.mimetype
    }
  });
});

// Get presigned upload URL (for frontend direct upload)
router.post('/presigned-url', authMiddleware, async (req, res) => {
  try {
    const { filename, contentType } = req.body;
    
    if (!filename || !contentType) {
      return res.status(400).json({ error: 'filename and contentType required' });
    }

    const ext = path.extname(filename);
    const key = `uploads/${Date.now()}-${uuidv4()}${ext}`;
    
    const uploadUrl = await s3Service.getSignedUploadUrl(key, contentType);

    res.json({
      uploadUrl,
      key,
      expiresIn: 3600
    });
  } catch (error) {
    console.error('Presigned URL error:', error);
    res.status(500).json({ error: 'Failed to generate URL' });
  }
});

// Get presigned download URL
router.get('/download/:key(*)', authMiddleware, async (req, res) => {
  try {
    const { key } = req.params;
    const downloadUrl = await s3Service.getSignedDownloadUrl(key);
    
    res.json({ downloadUrl });
  } catch (error) {
    console.error('Download URL error:', error);
    res.status(500).json({ error: 'Failed to generate download URL' });
  }
});

module.exports = router;
```

---

## 5️⃣ EXPERT LEVEL - Chunked Upload

### Chunked Upload Service

```javascript
// src/services/chunkedUpload.service.js
const fs = require('fs').promises;
const path = require('path');
const { v4: uuidv4 } = require('uuid');

class ChunkedUploadService {
  constructor() {
    this.sessions = new Map();
    this.tempDir = 'uploads/temp';
  }

  async initUpload(filename, totalChunks, userId) {
    const sessionId = uuidv4();
    const sessionDir = path.join(this.tempDir, sessionId);
    
    await fs.mkdir(sessionDir, { recursive: true });

    const session = {
      id: sessionId,
      filename,
      totalChunks,
      userId,
      receivedChunks: new Set(),
      tempDir: sessionDir,
      createdAt: new Date()
    };

    this.sessions.set(sessionId, session);

    return { sessionId, totalChunks };
  }

  async uploadChunk(sessionId, chunkIndex, chunkBuffer) {
    const session = this.sessions.get(sessionId);
    if (!session) {
      throw new Error('Invalid session');
    }

    const chunkPath = path.join(session.tempDir, `chunk_${chunkIndex}`);
    await fs.writeFile(chunkPath, chunkBuffer);

    session.receivedChunks.add(chunkIndex);

    return {
      chunkIndex,
      received: session.receivedChunks.size,
      total: session.totalChunks
    };
  }

  async completeUpload(sessionId) {
    const session = this.sessions.get(sessionId);
    if (!session) {
      throw new Error('Invalid session');
    }

    if (session.receivedChunks.size !== session.totalChunks) {
      throw new Error(`Missing chunks: received ${session.receivedChunks.size}/${session.totalChunks}`);
    }

    // Merge chunks
    const ext = path.extname(session.filename);
    const finalFilename = `${uuidv4()}${ext}`;
    const finalPath = path.join('uploads', finalFilename);

    const writeStream = require('fs').createWriteStream(finalPath);

    for (let i = 0; i < session.totalChunks; i++) {
      const chunkPath = path.join(session.tempDir, `chunk_${i}`);
      const chunkData = await fs.readFile(chunkPath);
      writeStream.write(chunkData);
    }

    writeStream.end();

    // Cleanup
    await fs.rm(session.tempDir, { recursive: true });
    this.sessions.delete(sessionId);

    return {
      filename: finalFilename,
      url: `/uploads/${finalFilename}`
    };
  }

  async cancelUpload(sessionId) {
    const session = this.sessions.get(sessionId);
    if (session) {
      await fs.rm(session.tempDir, { recursive: true, force: true });
      this.sessions.delete(sessionId);
    }
  }

  // Cleanup old sessions (run periodically)
  async cleanupOldSessions(maxAgeHours = 24) {
    const now = new Date();
    
    for (const [sessionId, session] of this.sessions) {
      const ageHours = (now - session.createdAt) / (1000 * 60 * 60);
      if (ageHours > maxAgeHours) {
        await this.cancelUpload(sessionId);
      }
    }
  }
}

module.exports = new ChunkedUploadService();
```

### Chunked Upload Routes

```javascript
// src/routes/chunkedUpload.routes.js
const express = require('express');
const router = express.Router();
const multer = require('multer');
const chunkedUploadService = require('../services/chunkedUpload.service');
const { authMiddleware } = require('../middleware/auth');

const upload = multer({ storage: multer.memoryStorage() });

// Initialize upload session
router.post('/init', authMiddleware, async (req, res) => {
  try {
    const { filename, totalChunks } = req.body;

    if (!filename || !totalChunks) {
      return res.status(400).json({ error: 'filename and totalChunks required' });
    }

    const result = await chunkedUploadService.initUpload(
      filename,
      totalChunks,
      req.user.id
    );

    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Upload chunk
router.post('/chunk', authMiddleware, upload.single('chunk'), async (req, res) => {
  try {
    const { sessionId, chunkIndex } = req.body;

    if (!sessionId || chunkIndex === undefined || !req.file) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const result = await chunkedUploadService.uploadChunk(
      sessionId,
      parseInt(chunkIndex),
      req.file.buffer
    );

    res.json(result);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Complete upload
router.post('/complete', authMiddleware, async (req, res) => {
  try {
    const { sessionId } = req.body;

    if (!sessionId) {
      return res.status(400).json({ error: 'sessionId required' });
    }

    const result = await chunkedUploadService.completeUpload(sessionId);
    res.json(result);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Cancel upload
router.delete('/:sessionId', authMiddleware, async (req, res) => {
  try {
    await chunkedUploadService.cancelUpload(req.params.sessionId);
    res.json({ message: 'Upload cancelled' });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

module.exports = router;
```

---

## 📋 Quick Reference

### File Upload Checklist

```
□ Validate file extension
□ Validate file size
□ Validate MIME type (read actual content)
□ Generate unique filename
□ Store securely
□ Process images asynchronously
□ Use presigned URLs for private S3 files
□ Cleanup temp files
□ Log all upload activities
```

### Common MIME Types

```javascript
const MIME_TYPES = {
  images: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  documents: [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ],
  spreadsheets: [
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ]
};
```

---

## 🔗 Related Docs

- [REDIS.md](REDIS.md) - Queue for async processing
- [SECURITY.md](../03-authentication/SECURITY.md) - File upload security
