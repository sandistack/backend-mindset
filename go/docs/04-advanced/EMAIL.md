# 📧 EMAIL - Go/Gin (Junior → Senior)

Dokumentasi lengkap tentang sending emails di Go, dari SMTP sederhana hingga templated async emails.

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

## 1️⃣ JUNIOR LEVEL - Basic Email with net/smtp

### Simple Email

```go
// internal/services/email_service.go
package services

import (
    "fmt"
    "net/smtp"
)

type EmailConfig struct {
    Host     string
    Port     int
    Username string
    Password string
    From     string
}

type EmailService struct {
    config EmailConfig
    auth   smtp.Auth
}

func NewEmailService(config EmailConfig) *EmailService {
    auth := smtp.PlainAuth("", config.Username, config.Password, config.Host)
    return &EmailService{
        config: config,
        auth:   auth,
    }
}

func (s *EmailService) SendSimple(to, subject, body string) error {
    msg := []byte(fmt.Sprintf(
        "To: %s\r\n"+
            "Subject: %s\r\n"+
            "MIME-Version: 1.0\r\n"+
            "Content-Type: text/plain; charset=utf-8\r\n"+
            "\r\n"+
            "%s",
        to, subject, body,
    ))

    addr := fmt.Sprintf("%s:%d", s.config.Host, s.config.Port)
    return smtp.SendMail(addr, s.auth, s.config.From, []string{to}, msg)
}
```

### Usage

```go
func main() {
    emailService := services.NewEmailService(services.EmailConfig{
        Host:     "smtp.gmail.com",
        Port:     587,
        Username: os.Getenv("SMTP_USERNAME"),
        Password: os.Getenv("SMTP_PASSWORD"),
        From:     "noreply@yourapp.com",
    })

    err := emailService.SendSimple(
        "user@example.com",
        "Welcome to Our App!",
        "Thank you for signing up.",
    )
    if err != nil {
        log.Printf("Failed to send email: %v", err)
    }
}
```

---

## 2️⃣ MID LEVEL - HTML Email with Templates

### Install gomail

```bash
go get gopkg.in/gomail.v2
```

### Enhanced Email Service

```go
// internal/services/email_service.go
package services

import (
    "bytes"
    "html/template"
    "path/filepath"

    "gopkg.in/gomail.v2"
)

type EmailService struct {
    dialer    *gomail.Dialer
    from      string
    templates *template.Template
}

func NewEmailService(host string, port int, username, password, from, templateDir string) (*EmailService, error) {
    dialer := gomail.NewDialer(host, port, username, password)

    // Load email templates
    templates, err := template.ParseGlob(filepath.Join(templateDir, "*.html"))
    if err != nil {
        return nil, fmt.Errorf("failed to parse templates: %w", err)
    }

    return &EmailService{
        dialer:    dialer,
        from:      from,
        templates: templates,
    }, nil
}

type Email struct {
    To          []string
    Subject     string
    Template    string
    Data        interface{}
    Attachments []Attachment
}

type Attachment struct {
    Filename string
    Path     string
}

func (s *EmailService) Send(email Email) error {
    // Render template
    var body bytes.Buffer
    if err := s.templates.ExecuteTemplate(&body, email.Template, email.Data); err != nil {
        return fmt.Errorf("failed to render template: %w", err)
    }

    // Create message
    m := gomail.NewMessage()
    m.SetHeader("From", s.from)
    m.SetHeader("To", email.To...)
    m.SetHeader("Subject", email.Subject)
    m.SetBody("text/html", body.String())

    // Add attachments
    for _, att := range email.Attachments {
        m.Attach(att.Path, gomail.Rename(att.Filename))
    }

    // Send
    if err := s.dialer.DialAndSend(m); err != nil {
        return fmt.Errorf("failed to send email: %w", err)
    }

    return nil
}
```

### Email Templates

```html
<!-- templates/emails/welcome.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
        }
        .header {
            background-color: #4A90D9;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .content {
            padding: 20px;
        }
        .button {
            display: inline-block;
            padding: 12px 24px;
            background-color: #4A90D9;
            color: white;
            text-decoration: none;
            border-radius: 4px;
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
        <h1>Welcome to {{.AppName}}!</h1>
    </div>
    
    <div class="content">
        <h2>Hi {{.User.FirstName}}!</h2>
        
        <p>Thank you for joining {{.AppName}}. We're excited to have you!</p>
        
        <p>Here's what you can do next:</p>
        <ul>
            <li>Complete your profile</li>
            <li>Explore our features</li>
            <li>Connect with others</li>
        </ul>
        
        <a href="{{.DashboardURL}}" class="button">Go to Dashboard</a>
    </div>
    
    <div class="footer">
        <p>&copy; {{.Year}} {{.AppName}}. All rights reserved.</p>
    </div>
</body>
</html>
```

```html
<!-- templates/emails/password_reset.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        /* Same styles as above */
    </style>
</head>
<body>
    <div class="header">
        <h1>Password Reset</h1>
    </div>
    
    <div class="content">
        <h2>Hi {{.User.FirstName}},</h2>
        
        <p>We received a request to reset your password.</p>
        
        <p>Click the button below to reset your password:</p>
        
        <a href="{{.ResetURL}}" class="button">Reset Password</a>
        
        <p><small>This link will expire in {{.ExpiryHours}} hours.</small></p>
        
        <p>If you didn't request this, you can safely ignore this email.</p>
    </div>
    
    <div class="footer">
        <p>&copy; {{.Year}} {{.AppName}}. All rights reserved.</p>
    </div>
</body>
</html>
```

### Helper Methods

```go
// internal/services/email_service.go

type WelcomeEmailData struct {
    AppName      string
    User         User
    DashboardURL string
    Year         int
}

func (s *EmailService) SendWelcome(user User, dashboardURL string) error {
    return s.Send(Email{
        To:       []string{user.Email},
        Subject:  fmt.Sprintf("Welcome to %s!", s.appName),
        Template: "welcome.html",
        Data: WelcomeEmailData{
            AppName:      s.appName,
            User:         user,
            DashboardURL: dashboardURL,
            Year:         time.Now().Year(),
        },
    })
}

type PasswordResetData struct {
    AppName     string
    User        User
    ResetURL    string
    ExpiryHours int
    Year        int
}

func (s *EmailService) SendPasswordReset(user User, resetToken string) error {
    resetURL := fmt.Sprintf("%s/reset-password?token=%s", s.baseURL, resetToken)

    return s.Send(Email{
        To:       []string{user.Email},
        Subject:  "Password Reset Request",
        Template: "password_reset.html",
        Data: PasswordResetData{
            AppName:     s.appName,
            User:        user,
            ResetURL:    resetURL,
            ExpiryHours: 24,
            Year:        time.Now().Year(),
        },
    })
}
```

---

## 3️⃣ MID-SENIOR LEVEL - Async Email with Goroutines

### Email Queue dengan Channels

```go
// internal/services/email_queue.go
package services

import (
    "context"
    "log"
    "sync"
)

type EmailQueue struct {
    emailService *EmailService
    queue        chan Email
    workers      int
    wg           sync.WaitGroup
}

func NewEmailQueue(emailService *EmailService, workers, bufferSize int) *EmailQueue {
    return &EmailQueue{
        emailService: emailService,
        queue:        make(chan Email, bufferSize),
        workers:      workers,
    }
}

func (q *EmailQueue) Start(ctx context.Context) {
    for i := 0; i < q.workers; i++ {
        q.wg.Add(1)
        go q.worker(ctx, i)
    }
    log.Printf("Started %d email workers", q.workers)
}

func (q *EmailQueue) worker(ctx context.Context, id int) {
    defer q.wg.Done()

    for {
        select {
        case <-ctx.Done():
            log.Printf("Email worker %d shutting down", id)
            return
        case email, ok := <-q.queue:
            if !ok {
                return
            }
            if err := q.emailService.Send(email); err != nil {
                log.Printf("Worker %d: Failed to send email to %v: %v", id, email.To, err)
                // Could implement retry logic here
            } else {
                log.Printf("Worker %d: Email sent to %v", id, email.To)
            }
        }
    }
}

func (q *EmailQueue) Enqueue(email Email) {
    q.queue <- email
}

func (q *EmailQueue) Stop() {
    close(q.queue)
    q.wg.Wait()
    log.Println("All email workers stopped")
}
```

### Usage with Queue

```go
// cmd/api/main.go
func main() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    emailService, _ := services.NewEmailService(/* config */)
    emailQueue := services.NewEmailQueue(emailService, 5, 100)
    emailQueue.Start(ctx)

    // In handler
    emailQueue.Enqueue(services.Email{
        To:       []string{"user@example.com"},
        Subject:  "Welcome!",
        Template: "welcome.html",
        Data:     welcomeData,
    })

    // Graceful shutdown
    // emailQueue.Stop()
}
```

### Email dengan Retry

```go
// internal/services/email_queue.go

type EmailJob struct {
    Email     Email
    Attempts  int
    MaxRetries int
    LastError  error
}

func (q *EmailQueue) workerWithRetry(ctx context.Context, id int) {
    defer q.wg.Done()

    for {
        select {
        case <-ctx.Done():
            return
        case job, ok := <-q.retryQueue:
            if !ok {
                return
            }

            err := q.emailService.Send(job.Email)
            if err != nil {
                job.Attempts++
                job.LastError = err

                if job.Attempts < job.MaxRetries {
                    // Exponential backoff
                    delay := time.Duration(job.Attempts*job.Attempts) * time.Second
                    time.AfterFunc(delay, func() {
                        q.retryQueue <- job
                    })
                    log.Printf("Worker %d: Retry %d for email to %v in %v",
                        id, job.Attempts, job.Email.To, delay)
                } else {
                    log.Printf("Worker %d: Max retries reached for email to %v: %v",
                        id, job.Email.To, err)
                    // Could send to dead letter queue or alert
                }
            } else {
                log.Printf("Worker %d: Email sent to %v (attempt %d)",
                    id, job.Email.To, job.Attempts+1)
            }
        }
    }
}
```

---

## 4️⃣ SENIOR LEVEL - SendGrid & Mailgun Integration

### SendGrid Service

```bash
go get github.com/sendgrid/sendgrid-go
```

```go
// internal/services/sendgrid_service.go
package services

import (
    "fmt"

    "github.com/sendgrid/sendgrid-go"
    "github.com/sendgrid/sendgrid-go/helpers/mail"
)

type SendGridService struct {
    client    *sendgrid.Client
    fromEmail string
    fromName  string
}

func NewSendGridService(apiKey, fromEmail, fromName string) *SendGridService {
    return &SendGridService{
        client:    sendgrid.NewSendClient(apiKey),
        fromEmail: fromEmail,
        fromName:  fromName,
    }
}

type SendGridEmail struct {
    To          string
    ToName      string
    Subject     string
    HTMLContent string
    TextContent string
    Categories  []string
}

func (s *SendGridService) Send(email SendGridEmail) error {
    from := mail.NewEmail(s.fromName, s.fromEmail)
    to := mail.NewEmail(email.ToName, email.To)

    message := mail.NewSingleEmail(from, email.Subject, to, email.TextContent, email.HTMLContent)

    // Add categories for analytics
    for _, category := range email.Categories {
        message.AddCategories(category)
    }

    response, err := s.client.Send(message)
    if err != nil {
        return fmt.Errorf("sendgrid error: %w", err)
    }

    if response.StatusCode >= 400 {
        return fmt.Errorf("sendgrid error: status %d, body: %s",
            response.StatusCode, response.Body)
    }

    return nil
}

// Send using SendGrid Dynamic Templates
func (s *SendGridService) SendWithTemplate(to, toName, templateID string, dynamicData map[string]interface{}) error {
    m := mail.NewV3Mail()
    m.SetFrom(mail.NewEmail(s.fromName, s.fromEmail))
    m.SetTemplateID(templateID)

    p := mail.NewPersonalization()
    p.AddTos(mail.NewEmail(toName, to))

    for key, value := range dynamicData {
        p.SetDynamicTemplateData(key, value)
    }

    m.AddPersonalizations(p)

    response, err := s.client.Send(m)
    if err != nil {
        return err
    }

    if response.StatusCode >= 400 {
        return fmt.Errorf("sendgrid error: %d", response.StatusCode)
    }

    return nil
}
```

### Mailgun Service

```bash
go get github.com/mailgun/mailgun-go/v4
```

```go
// internal/services/mailgun_service.go
package services

import (
    "context"
    "time"

    "github.com/mailgun/mailgun-go/v4"
)

type MailgunService struct {
    mg     *mailgun.MailgunImpl
    domain string
    from   string
}

func NewMailgunService(domain, apiKey, from string) *MailgunService {
    mg := mailgun.NewMailgun(domain, apiKey)
    return &MailgunService{
        mg:     mg,
        domain: domain,
        from:   from,
    }
}

func (s *MailgunService) Send(ctx context.Context, to, subject, htmlBody string, tags []string) (string, error) {
    message := s.mg.NewMessage(s.from, subject, "", to)
    message.SetHtml(htmlBody)

    for _, tag := range tags {
        message.AddTag(tag)
    }

    ctx, cancel := context.WithTimeout(ctx, 10*time.Second)
    defer cancel()

    _, id, err := s.mg.Send(ctx, message)
    if err != nil {
        return "", err
    }

    return id, nil
}

func (s *MailgunService) SendWithTemplate(ctx context.Context, to, subject, templateName string, variables map[string]interface{}) (string, error) {
    message := s.mg.NewMessage(s.from, subject, "")
    message.AddRecipient(to)
    message.SetTemplate(templateName)

    for key, value := range variables {
        message.AddVariable(key, value)
    }

    ctx, cancel := context.WithTimeout(ctx, 10*time.Second)
    defer cancel()

    _, id, err := s.mg.Send(ctx, message)
    return id, err
}
```

---

## 5️⃣ EXPERT LEVEL - Email Tracking & Logging

### Email Log Model

```go
// internal/models/email_log.go
package models

import (
    "time"

    "gorm.io/gorm"
)

type EmailStatus string

const (
    EmailStatusPending   EmailStatus = "pending"
    EmailStatusSent      EmailStatus = "sent"
    EmailStatusDelivered EmailStatus = "delivered"
    EmailStatusOpened    EmailStatus = "opened"
    EmailStatusClicked   EmailStatus = "clicked"
    EmailStatusBounced   EmailStatus = "bounced"
    EmailStatusFailed    EmailStatus = "failed"
)

type EmailLog struct {
    gorm.Model
    Recipient   string      `gorm:"index"`
    Subject     string
    Template    string
    Status      EmailStatus `gorm:"index"`
    MessageID   string      `gorm:"index"`
    Provider    string      // sendgrid, mailgun, smtp
    
    SentAt      *time.Time
    DeliveredAt *time.Time
    OpenedAt    *time.Time
    ClickedAt   *time.Time
    
    ErrorMessage string
    Metadata     JSON `gorm:"type:jsonb"`
}
```

### Trackable Email Service

```go
// internal/services/trackable_email_service.go
package services

import (
    "context"
    "time"

    "myapp/internal/models"
    "myapp/internal/repositories"
)

type TrackableEmailService struct {
    provider  EmailProvider
    emailRepo *repositories.EmailLogRepository
}

type EmailProvider interface {
    Send(ctx context.Context, email Email) (messageID string, err error)
}

func NewTrackableEmailService(provider EmailProvider, repo *repositories.EmailLogRepository) *TrackableEmailService {
    return &TrackableEmailService{
        provider:  provider,
        emailRepo: repo,
    }
}

func (s *TrackableEmailService) Send(ctx context.Context, email Email) error {
    // Create log entry
    log := &models.EmailLog{
        Recipient: email.To[0],
        Subject:   email.Subject,
        Template:  email.Template,
        Status:    models.EmailStatusPending,
    }
    s.emailRepo.Create(log)

    // Send email
    messageID, err := s.provider.Send(ctx, email)
    if err != nil {
        log.Status = models.EmailStatusFailed
        log.ErrorMessage = err.Error()
        s.emailRepo.Update(log)
        return err
    }

    // Update log
    now := time.Now()
    log.Status = models.EmailStatusSent
    log.MessageID = messageID
    log.SentAt = &now
    s.emailRepo.Update(log)

    return nil
}

func (s *TrackableEmailService) HandleWebhook(event WebhookEvent) error {
    log, err := s.emailRepo.FindByMessageID(event.MessageID)
    if err != nil {
        return err
    }

    now := time.Now()
    
    switch event.Type {
    case "delivered":
        log.Status = models.EmailStatusDelivered
        log.DeliveredAt = &now
    case "open":
        log.Status = models.EmailStatusOpened
        log.OpenedAt = &now
    case "click":
        log.Status = models.EmailStatusClicked
        log.ClickedAt = &now
    case "bounce":
        log.Status = models.EmailStatusBounced
        log.ErrorMessage = event.Reason
    }

    return s.emailRepo.Update(log)
}
```

### Webhook Handler

```go
// internal/handlers/webhook.go
package handlers

import (
    "net/http"

    "github.com/gin-gonic/gin"
)

type WebhookHandler struct {
    emailService *services.TrackableEmailService
}

func (h *WebhookHandler) SendGridWebhook(c *gin.Context) {
    var events []struct {
        Event     string `json:"event"`
        MessageID string `json:"sg_message_id"`
        Reason    string `json:"reason"`
    }

    if err := c.ShouldBindJSON(&events); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    for _, event := range events {
        h.emailService.HandleWebhook(services.WebhookEvent{
            Type:      event.Event,
            MessageID: event.MessageID,
            Reason:    event.Reason,
        })
    }

    c.JSON(http.StatusOK, gin.H{"status": "ok"})
}
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
□ Use async sending (goroutines/queue)
□ Validate email addresses
□ Handle bounces and errors
□ Include unsubscribe link
□ Log all sent emails
□ Set up webhooks for tracking
□ Implement retry with backoff
□ Rate limit bulk sending
□ Use templates for consistency
```

---

## 🔗 Related Docs

- [CONCURRENCY.md](CONCURRENCY.md) - Goroutines for async email
- [LOGGING.md](../06-operations/LOGGING.md) - Email logging
