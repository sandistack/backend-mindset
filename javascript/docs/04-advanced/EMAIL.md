# 📧 EMAIL - Express.js (Junior → Senior)

Dokumentasi lengkap tentang sending emails di Express dengan Nodemailer, dari SMTP sederhana hingga templated async emails.

---

## 🎯 Kapan Butuh Email?

```
Use Cases:
✅ Welcome email setelah register
✅ Password reset
✅ Email verification
✅ Order confirmation
✅ Notification alerts
✅ Weekly reports
```

---

## 1️⃣ JUNIOR LEVEL - Basic Email dengan Nodemailer

### Install Dependencies

```bash
npm install nodemailer
```

### Basic Email Service

```javascript
// src/services/email.service.js
const nodemailer = require('nodemailer');

class EmailService {
  constructor() {
    this.transporter = nodemailer.createTransport({
      host: process.env.SMTP_HOST || 'smtp.gmail.com',
      port: parseInt(process.env.SMTP_PORT) || 587,
      secure: false, // true for 465, false for other ports
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS
      }
    });

    this.from = process.env.EMAIL_FROM || 'noreply@yourapp.com';
  }

  async send(to, subject, text, html = null) {
    const mailOptions = {
      from: this.from,
      to,
      subject,
      text,
      html: html || text
    };

    try {
      const info = await this.transporter.sendMail(mailOptions);
      console.log('Email sent:', info.messageId);
      return { success: true, messageId: info.messageId };
    } catch (error) {
      console.error('Email error:', error);
      return { success: false, error: error.message };
    }
  }

  async sendWelcome(user) {
    const subject = 'Welcome to Our App!';
    const text = `Hi ${user.name},\n\nThank you for joining us!`;
    const html = `
      <h1>Welcome, ${user.name}!</h1>
      <p>Thank you for joining us.</p>
      <a href="${process.env.BASE_URL}/dashboard">Go to Dashboard</a>
    `;

    return this.send(user.email, subject, text, html);
  }

  async sendPasswordReset(user, resetToken) {
    const resetUrl = `${process.env.BASE_URL}/reset-password?token=${resetToken}`;
    const subject = 'Password Reset Request';
    const text = `Click this link to reset your password: ${resetUrl}`;
    const html = `
      <h2>Password Reset</h2>
      <p>Click the button below to reset your password:</p>
      <a href="${resetUrl}" style="padding: 10px 20px; background: #4A90D9; color: white; text-decoration: none; border-radius: 4px;">
        Reset Password
      </a>
      <p><small>This link expires in 1 hour.</small></p>
    `;

    return this.send(user.email, subject, text, html);
  }
}

module.exports = new EmailService();
```

### Usage in Controller

```javascript
// src/controllers/auth.controller.js
const emailService = require('../services/email.service');

exports.register = async (req, res) => {
  try {
    // Create user
    const user = await prisma.user.create({
      data: req.body
    });

    // Send welcome email
    await emailService.sendWelcome(user);

    res.status(201).json({
      message: 'Registration successful',
      user
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
```

---

## 2️⃣ MID LEVEL - Email Templates

### Install Template Engine

```bash
npm install handlebars
```

### Template-based Email Service

```javascript
// src/services/email.service.js
const nodemailer = require('nodemailer');
const handlebars = require('handlebars');
const fs = require('fs').promises;
const path = require('path');

class EmailService {
  constructor() {
    this.transporter = nodemailer.createTransport({
      host: process.env.SMTP_HOST,
      port: parseInt(process.env.SMTP_PORT) || 587,
      secure: process.env.SMTP_SECURE === 'true',
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS
      }
    });

    this.from = process.env.EMAIL_FROM;
    this.appName = process.env.APP_NAME || 'YourApp';
    this.baseUrl = process.env.BASE_URL;
    this.templatesDir = path.join(__dirname, '../templates/emails');
    this.templateCache = new Map();
  }

  async loadTemplate(templateName) {
    // Check cache
    if (this.templateCache.has(templateName)) {
      return this.templateCache.get(templateName);
    }

    const templatePath = path.join(this.templatesDir, `${templateName}.hbs`);
    const templateSource = await fs.readFile(templatePath, 'utf8');
    const template = handlebars.compile(templateSource);

    this.templateCache.set(templateName, template);
    return template;
  }

  async send(options) {
    const { to, subject, template, data, attachments } = options;

    // Load and render template
    const templateFn = await this.loadTemplate(template);
    const html = templateFn({
      ...data,
      appName: this.appName,
      baseUrl: this.baseUrl,
      year: new Date().getFullYear()
    });

    const mailOptions = {
      from: `${this.appName} <${this.from}>`,
      to,
      subject,
      html,
      attachments
    };

    try {
      const info = await this.transporter.sendMail(mailOptions);
      return { success: true, messageId: info.messageId };
    } catch (error) {
      console.error('Email error:', error);
      throw error;
    }
  }

  async sendWelcome(user) {
    return this.send({
      to: user.email,
      subject: `Welcome to ${this.appName}!`,
      template: 'welcome',
      data: {
        user,
        dashboardUrl: `${this.baseUrl}/dashboard`
      }
    });
  }

  async sendPasswordReset(user, resetToken) {
    return this.send({
      to: user.email,
      subject: 'Password Reset Request',
      template: 'password-reset',
      data: {
        user,
        resetUrl: `${this.baseUrl}/reset-password?token=${resetToken}`,
        expiryHours: 1
      }
    });
  }

  async sendVerification(user, verificationToken) {
    return this.send({
      to: user.email,
      subject: 'Verify Your Email',
      template: 'verify-email',
      data: {
        user,
        verifyUrl: `${this.baseUrl}/verify-email?token=${verificationToken}`
      }
    });
  }

  async sendWithAttachment(to, subject, template, data, attachments) {
    return this.send({
      to,
      subject,
      template,
      data,
      attachments: attachments.map(att => ({
        filename: att.filename,
        path: att.path,
        contentType: att.contentType
      }))
    });
  }
}

module.exports = new EmailService();
```

### Email Templates

```handlebars
{{!-- src/templates/emails/layout.hbs --}}
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      font-family: Arial, sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 600px;
      margin: 0 auto;
      padding: 20px;
    }
    .header {
      background-color: #4A90D9;
      color: white;
      padding: 20px;
      text-align: center;
    }
    .content {
      padding: 20px;
      background-color: #f9f9f9;
    }
    .button {
      display: inline-block;
      padding: 12px 24px;
      background-color: #4A90D9;
      color: white;
      text-decoration: none;
      border-radius: 4px;
      margin: 20px 0;
    }
    .footer {
      padding: 20px;
      text-align: center;
      font-size: 12px;
      color: #666;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>{{appName}}</h1>
  </div>
  <div class="content">
    {{{body}}}
  </div>
  <div class="footer">
    <p>&copy; {{year}} {{appName}}. All rights reserved.</p>
  </div>
</body>
</html>
```

```handlebars
{{!-- src/templates/emails/welcome.hbs --}}
<h2>Welcome, {{user.name}}!</h2>

<p>Thank you for joining {{appName}}. We're excited to have you!</p>

<p>Here's what you can do next:</p>
<ul>
  <li>Complete your profile</li>
  <li>Explore our features</li>
  <li>Connect with others</li>
</ul>

<a href="{{dashboardUrl}}" class="button">Go to Dashboard</a>

<p>If you have any questions, just reply to this email.</p>

<p>Best regards,<br>The {{appName}} Team</p>
```

```handlebars
{{!-- src/templates/emails/password-reset.hbs --}}
<h2>Password Reset Request</h2>

<p>Hi {{user.name}},</p>

<p>We received a request to reset your password.</p>

<p>Click the button below to reset your password:</p>

<a href="{{resetUrl}}" class="button">Reset Password</a>

<p><small>This link will expire in {{expiryHours}} hour(s).</small></p>

<p>If you didn't request this, you can safely ignore this email.</p>
```

---

## 3️⃣ MID-SENIOR LEVEL - Async Email dengan Queue

### Install BullMQ

```bash
npm install bullmq
```

### Email Queue

```javascript
// src/queues/email.queue.js
const { Queue, Worker } = require('bullmq');
const emailService = require('../services/email.service');

const connection = {
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT) || 6379
};

// Create queue
const emailQueue = new Queue('email', { connection });

// Create worker
const emailWorker = new Worker('email', async (job) => {
  const { type, data } = job.data;

  console.log(`Processing email job: ${type}`);

  try {
    switch (type) {
      case 'welcome':
        await emailService.sendWelcome(data.user);
        break;
      case 'password-reset':
        await emailService.sendPasswordReset(data.user, data.resetToken);
        break;
      case 'verification':
        await emailService.sendVerification(data.user, data.verificationToken);
        break;
      case 'custom':
        await emailService.send(data);
        break;
      default:
        throw new Error(`Unknown email type: ${type}`);
    }

    return { success: true };
  } catch (error) {
    console.error(`Email job failed: ${error.message}`);
    throw error;
  }
}, {
  connection,
  concurrency: 5 // Process 5 emails at a time
});

// Event handlers
emailWorker.on('completed', (job) => {
  console.log(`Email job ${job.id} completed`);
});

emailWorker.on('failed', (job, error) => {
  console.error(`Email job ${job.id} failed:`, error.message);
});

// Helper functions
const queueEmail = async (type, data, options = {}) => {
  return emailQueue.add(type, { type, data }, {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 1000
    },
    ...options
  });
};

const queueWelcomeEmail = async (user) => {
  return queueEmail('welcome', { user });
};

const queuePasswordResetEmail = async (user, resetToken) => {
  return queueEmail('password-reset', { user, resetToken });
};

const queueVerificationEmail = async (user, verificationToken) => {
  return queueEmail('verification', { user, verificationToken });
};

module.exports = {
  emailQueue,
  emailWorker,
  queueEmail,
  queueWelcomeEmail,
  queuePasswordResetEmail,
  queueVerificationEmail
};
```

### Usage in Controller

```javascript
// src/controllers/auth.controller.js
const { queueWelcomeEmail, queuePasswordResetEmail } = require('../queues/email.queue');

exports.register = async (req, res) => {
  try {
    const user = await prisma.user.create({
      data: req.body
    });

    // Queue welcome email (non-blocking)
    await queueWelcomeEmail(user);

    res.status(201).json({
      message: 'Registration successful',
      user
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

exports.forgotPassword = async (req, res) => {
  try {
    const { email } = req.body;
    const user = await prisma.user.findUnique({ where: { email } });

    if (!user) {
      // Don't reveal if user exists
      return res.json({ message: 'If email exists, reset link will be sent' });
    }

    const resetToken = generateResetToken();
    
    // Save token to database
    await prisma.passwordReset.create({
      data: {
        userId: user.id,
        token: resetToken,
        expiresAt: new Date(Date.now() + 3600000) // 1 hour
      }
    });

    // Queue password reset email
    await queuePasswordResetEmail(user, resetToken);

    res.json({ message: 'If email exists, reset link will be sent' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
```

### Scheduled Emails

```javascript
// src/queues/scheduledEmail.queue.js
const { Queue, Worker } = require('bullmq');
const emailService = require('../services/email.service');
const prisma = require('../lib/prisma');

const connection = {
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT) || 6379
};

const scheduledEmailQueue = new Queue('scheduled-email', { connection });

// Schedule weekly digest
const scheduleWeeklyDigest = async () => {
  await scheduledEmailQueue.add(
    'weekly-digest',
    {},
    {
      repeat: {
        pattern: '0 9 * * 1' // Every Monday at 9 AM
      }
    }
  );
};

// Worker
const scheduledEmailWorker = new Worker('scheduled-email', async (job) => {
  if (job.name === 'weekly-digest') {
    const users = await prisma.user.findMany({
      where: { subscribed: true }
    });

    for (const user of users) {
      const stats = await getUserWeeklyStats(user.id);
      
      await emailService.send({
        to: user.email,
        subject: 'Your Weekly Summary',
        template: 'weekly-digest',
        data: { user, stats }
      });
    }
  }
}, { connection });

module.exports = {
  scheduledEmailQueue,
  scheduleWeeklyDigest
};
```

---

## 4️⃣ SENIOR LEVEL - SendGrid & Mailgun

### SendGrid

```bash
npm install @sendgrid/mail
```

```javascript
// src/services/sendgrid.service.js
const sgMail = require('@sendgrid/mail');

class SendGridService {
  constructor() {
    sgMail.setApiKey(process.env.SENDGRID_API_KEY);
    this.from = process.env.EMAIL_FROM;
  }

  async send(options) {
    const { to, subject, html, text, templateId, dynamicData, attachments } = options;

    const msg = {
      to,
      from: this.from,
      subject
    };

    if (templateId) {
      // Use SendGrid Dynamic Template
      msg.templateId = templateId;
      msg.dynamicTemplateData = dynamicData;
    } else {
      msg.html = html;
      msg.text = text;
    }

    if (attachments) {
      msg.attachments = attachments.map(att => ({
        content: att.content.toString('base64'),
        filename: att.filename,
        type: att.contentType,
        disposition: 'attachment'
      }));
    }

    try {
      const response = await sgMail.send(msg);
      return {
        success: true,
        messageId: response[0].headers['x-message-id']
      };
    } catch (error) {
      console.error('SendGrid error:', error.response?.body || error);
      throw error;
    }
  }

  async sendWithTemplate(to, templateId, dynamicData) {
    return this.send({
      to,
      templateId,
      dynamicData
    });
  }

  async sendBulk(messages) {
    try {
      await sgMail.send(messages);
      return { success: true };
    } catch (error) {
      console.error('SendGrid bulk error:', error);
      throw error;
    }
  }
}

module.exports = new SendGridService();
```

### Mailgun

```bash
npm install mailgun.js form-data
```

```javascript
// src/services/mailgun.service.js
const formData = require('form-data');
const Mailgun = require('mailgun.js');

class MailgunService {
  constructor() {
    const mailgun = new Mailgun(formData);
    this.mg = mailgun.client({
      username: 'api',
      key: process.env.MAILGUN_API_KEY
    });
    this.domain = process.env.MAILGUN_DOMAIN;
    this.from = process.env.EMAIL_FROM;
  }

  async send(options) {
    const { to, subject, html, text, attachments, tags } = options;

    const msgData = {
      from: this.from,
      to: Array.isArray(to) ? to : [to],
      subject,
      html,
      text
    };

    if (tags) {
      msgData['o:tag'] = tags;
    }

    if (attachments) {
      msgData.attachment = attachments.map(att => ({
        filename: att.filename,
        data: att.content
      }));
    }

    try {
      const response = await this.mg.messages.create(this.domain, msgData);
      return {
        success: true,
        messageId: response.id
      };
    } catch (error) {
      console.error('Mailgun error:', error);
      throw error;
    }
  }

  async sendWithTemplate(to, templateName, variables) {
    const msgData = {
      from: this.from,
      to,
      template: templateName,
      'h:X-Mailgun-Variables': JSON.stringify(variables)
    };

    const response = await this.mg.messages.create(this.domain, msgData);
    return { success: true, messageId: response.id };
  }
}

module.exports = new MailgunService();
```

---

## 5️⃣ EXPERT LEVEL - Email Tracking

### Email Log Model (Prisma)

```prisma
// prisma/schema.prisma
model EmailLog {
  id          String   @id @default(uuid())
  recipient   String
  subject     String
  template    String
  status      EmailStatus @default(PENDING)
  messageId   String?
  provider    String   // sendgrid, mailgun, smtp
  
  sentAt      DateTime?
  deliveredAt DateTime?
  openedAt    DateTime?
  clickedAt   DateTime?
  
  errorMessage String?
  metadata    Json?
  
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@index([recipient, status])
  @@index([createdAt])
}

enum EmailStatus {
  PENDING
  SENT
  DELIVERED
  OPENED
  CLICKED
  BOUNCED
  FAILED
}
```

### Trackable Email Service

```javascript
// src/services/trackableEmail.service.js
const prisma = require('../lib/prisma');
const sendgridService = require('./sendgrid.service');

class TrackableEmailService {
  async send(options) {
    const { to, subject, template, data, provider = 'sendgrid' } = options;

    // Create log entry
    const log = await prisma.emailLog.create({
      data: {
        recipient: to,
        subject,
        template,
        provider,
        status: 'PENDING'
      }
    });

    try {
      let result;

      if (provider === 'sendgrid') {
        result = await sendgridService.send(options);
      } else {
        // Use other provider
      }

      // Update log with success
      await prisma.emailLog.update({
        where: { id: log.id },
        data: {
          status: 'SENT',
          messageId: result.messageId,
          sentAt: new Date()
        }
      });

      return result;
    } catch (error) {
      // Update log with failure
      await prisma.emailLog.update({
        where: { id: log.id },
        data: {
          status: 'FAILED',
          errorMessage: error.message
        }
      });

      throw error;
    }
  }

  async handleWebhook(event) {
    const { messageId, eventType, timestamp } = event;

    const log = await prisma.emailLog.findFirst({
      where: { messageId }
    });

    if (!log) return;

    const updateData = {};

    switch (eventType) {
      case 'delivered':
        updateData.status = 'DELIVERED';
        updateData.deliveredAt = new Date(timestamp);
        break;
      case 'open':
        updateData.status = 'OPENED';
        updateData.openedAt = new Date(timestamp);
        break;
      case 'click':
        updateData.status = 'CLICKED';
        updateData.clickedAt = new Date(timestamp);
        break;
      case 'bounce':
        updateData.status = 'BOUNCED';
        break;
    }

    await prisma.emailLog.update({
      where: { id: log.id },
      data: updateData
    });
  }
}

module.exports = new TrackableEmailService();
```

### Webhook Handler

```javascript
// src/routes/webhook.routes.js
const express = require('express');
const router = express.Router();
const trackableEmailService = require('../services/trackableEmail.service');

// SendGrid webhook
router.post('/sendgrid', async (req, res) => {
  try {
    const events = req.body;

    for (const event of events) {
      await trackableEmailService.handleWebhook({
        messageId: event.sg_message_id?.split('.')[0],
        eventType: event.event,
        timestamp: event.timestamp * 1000
      });
    }

    res.json({ status: 'ok' });
  } catch (error) {
    console.error('Webhook error:', error);
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
```

---

## 📋 Quick Reference

### Email Providers Comparison

| Provider | Free Tier | Best For |
|----------|-----------|----------|
| **SendGrid** | 100/day | Transactional + Marketing |
| **Mailgun** | 5,000/mo | Developers |
| **Amazon SES** | 62,000/mo | High volume |
| **Postmark** | 100/mo | Transactional |

### Email Checklist

```
□ Use async sending (queue)
□ Validate email addresses
□ Handle bounces
□ Include unsubscribe link
□ Log all sent emails
□ Set up webhooks for tracking
□ Implement retry with backoff
□ Use templates for consistency
```

---

## 🔗 Related Docs

- [REDIS.md](REDIS.md) - Queue for async email
- [LOGGING.md](../06-operations/LOGGING.md) - Email logging
