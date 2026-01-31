# 📊 EXPORT - Go/Gin (Junior → Senior)

Dokumentasi lengkap tentang export data ke berbagai format: CSV, Excel, dan PDF.

---

## 🎯 Kapan Butuh Export?

```
Use Cases:
✅ Export laporan (PDF)
✅ Download data (CSV/Excel)
✅ Generate invoice (PDF)
✅ Backup data (CSV)
✅ Analytics reports (Excel)
```

---

## 1️⃣ JUNIOR LEVEL - CSV Export

### Simple CSV Export

```go
// internal/handlers/export.go
package handlers

import (
    "encoding/csv"
    "fmt"
    "net/http"
    "time"

    "github.com/gin-gonic/gin"
    "myapp/internal/models"
    "myapp/internal/repositories"
)

type ExportHandler struct {
    taskRepo *repositories.TaskRepository
}

func NewExportHandler(taskRepo *repositories.TaskRepository) *ExportHandler {
    return &ExportHandler{taskRepo: taskRepo}
}

func (h *ExportHandler) ExportTasksCSV(c *gin.Context) {
    userID := c.GetUint("user_id")

    // Get data
    tasks, err := h.taskRepo.FindByUserID(userID)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch tasks"})
        return
    }

    // Set headers for CSV download
    filename := fmt.Sprintf("tasks_%s.csv", time.Now().Format("20060102"))
    c.Header("Content-Type", "text/csv")
    c.Header("Content-Disposition", fmt.Sprintf("attachment; filename=%s", filename))

    // Create CSV writer
    writer := csv.NewWriter(c.Writer)
    defer writer.Flush()

    // Write header
    headers := []string{"ID", "Title", "Description", "Status", "Priority", "Created At"}
    writer.Write(headers)

    // Write data
    for _, task := range tasks {
        row := []string{
            fmt.Sprintf("%d", task.ID),
            task.Title,
            task.Description,
            task.Status,
            task.Priority,
            task.CreatedAt.Format("2006-01-02 15:04:05"),
        }
        writer.Write(row)
    }
}
```

### CSV with Filters

```go
func (h *ExportHandler) ExportTasksCSVFiltered(c *gin.Context) {
    userID := c.GetUint("user_id")
    status := c.Query("status")
    priority := c.Query("priority")
    dateFrom := c.Query("date_from")
    dateTo := c.Query("date_to")

    // Build filter
    filter := repositories.TaskFilter{
        UserID:   userID,
        Status:   status,
        Priority: priority,
    }

    if dateFrom != "" {
        t, _ := time.Parse("2006-01-02", dateFrom)
        filter.DateFrom = &t
    }
    if dateTo != "" {
        t, _ := time.Parse("2006-01-02", dateTo)
        filter.DateTo = &t
    }

    tasks, err := h.taskRepo.FindWithFilter(filter)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch tasks"})
        return
    }

    // Set headers
    c.Header("Content-Type", "text/csv; charset=utf-8")
    c.Header("Content-Disposition", "attachment; filename=tasks_export.csv")

    // Write BOM for Excel compatibility
    c.Writer.Write([]byte{0xEF, 0xBB, 0xBF})

    writer := csv.NewWriter(c.Writer)
    defer writer.Flush()

    writer.Write([]string{"ID", "Title", "Description", "Status", "Priority", "Created At"})

    for _, task := range tasks {
        writer.Write([]string{
            fmt.Sprintf("%d", task.ID),
            task.Title,
            task.Description,
            task.Status,
            task.Priority,
            task.CreatedAt.Format("2006-01-02 15:04:05"),
        })
    }
}
```

---

## 2️⃣ MID LEVEL - Excel Export

### Install excelize

```bash
go get github.com/xuri/excelize/v2
```

### Excel Service

```go
// internal/services/excel_service.go
package services

import (
    "fmt"

    "github.com/xuri/excelize/v2"
)

type ExcelService struct {
    file      *excelize.File
    sheetName string
    row       int
}

func NewExcelService(sheetName string) *ExcelService {
    f := excelize.NewFile()
    f.SetSheetName("Sheet1", sheetName)

    return &ExcelService{
        file:      f,
        sheetName: sheetName,
        row:       1,
    }
}

// Header style
func (s *ExcelService) headerStyle() int {
    style, _ := s.file.NewStyle(&excelize.Style{
        Font: &excelize.Font{
            Bold:  true,
            Color: "#FFFFFF",
            Size:  11,
        },
        Fill: excelize.Fill{
            Type:    "pattern",
            Color:   []string{"#4472C4"},
            Pattern: 1,
        },
        Alignment: &excelize.Alignment{
            Horizontal: "center",
            Vertical:   "center",
        },
        Border: []excelize.Border{
            {Type: "left", Color: "#000000", Style: 1},
            {Type: "top", Color: "#000000", Style: 1},
            {Type: "right", Color: "#000000", Style: 1},
            {Type: "bottom", Color: "#000000", Style: 1},
        },
    })
    return style
}

// Data style
func (s *ExcelService) dataStyle() int {
    style, _ := s.file.NewStyle(&excelize.Style{
        Border: []excelize.Border{
            {Type: "left", Color: "#000000", Style: 1},
            {Type: "top", Color: "#000000", Style: 1},
            {Type: "right", Color: "#000000", Style: 1},
            {Type: "bottom", Color: "#000000", Style: 1},
        },
        Alignment: &excelize.Alignment{
            Vertical: "center",
        },
    })
    return style
}

func (s *ExcelService) WriteHeader(headers []string) {
    headerStyle := s.headerStyle()

    for col, header := range headers {
        cell, _ := excelize.CoordinatesToCellName(col+1, s.row)
        s.file.SetCellValue(s.sheetName, cell, header)
        s.file.SetCellStyle(s.sheetName, cell, cell, headerStyle)
    }
    s.row++
}

func (s *ExcelService) WriteRow(data []interface{}) {
    dataStyle := s.dataStyle()

    for col, value := range data {
        cell, _ := excelize.CoordinatesToCellName(col+1, s.row)
        s.file.SetCellValue(s.sheetName, cell, value)
        s.file.SetCellStyle(s.sheetName, cell, cell, dataStyle)
    }
    s.row++
}

func (s *ExcelService) AutoWidth(columns int) {
    for col := 1; col <= columns; col++ {
        colName, _ := excelize.ColumnNumberToName(col)
        s.file.SetColWidth(s.sheetName, colName, colName, 15)
    }
}

func (s *ExcelService) AddSheet(name string) {
    s.file.NewSheet(name)
    s.sheetName = name
    s.row = 1
}

func (s *ExcelService) GetBuffer() (*bytes.Buffer, error) {
    buffer := new(bytes.Buffer)
    err := s.file.Write(buffer)
    return buffer, err
}

func (s *ExcelService) SaveToFile(path string) error {
    return s.file.SaveAs(path)
}
```

### Excel Export Handler

```go
// internal/handlers/export.go
func (h *ExportHandler) ExportTasksExcel(c *gin.Context) {
    userID := c.GetUint("user_id")

    tasks, err := h.taskRepo.FindByUserID(userID)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch tasks"})
        return
    }

    excel := services.NewExcelService("Tasks")

    // Write header
    excel.WriteHeader([]string{"ID", "Title", "Description", "Status", "Priority", "Created At"})

    // Write data
    for _, task := range tasks {
        excel.WriteRow([]interface{}{
            task.ID,
            task.Title,
            task.Description,
            task.Status,
            task.Priority,
            task.CreatedAt.Format("2006-01-02 15:04"),
        })
    }

    excel.AutoWidth(6)

    // Get buffer
    buffer, err := excel.GetBuffer()
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate Excel"})
        return
    }

    filename := fmt.Sprintf("tasks_%s.xlsx", time.Now().Format("20060102"))
    c.Header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    c.Header("Content-Disposition", fmt.Sprintf("attachment; filename=%s", filename))
    c.Data(http.StatusOK, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", buffer.Bytes())
}
```

### Multi-Sheet Report

```go
func (h *ExportHandler) ExportMonthlyReport(c *gin.Context) {
    excel := services.NewExcelService("Summary")

    // Sheet 1: Summary
    excel.WriteHeader([]string{"Metric", "Value"})
    
    totalUsers, _ := h.userRepo.Count()
    totalTasks, _ := h.taskRepo.Count()
    completedTasks, _ := h.taskRepo.CountByStatus("done")

    excel.WriteRow([]interface{}{"Total Users", totalUsers})
    excel.WriteRow([]interface{}{"Total Tasks", totalTasks})
    excel.WriteRow([]interface{}{"Completed Tasks", completedTasks})
    excel.AutoWidth(2)

    // Sheet 2: Tasks by User
    excel.AddSheet("Tasks by User")
    excel.WriteHeader([]string{"User", "Total", "Completed", "Pending"})

    userStats, _ := h.taskRepo.GetUserStats()
    for _, stat := range userStats {
        excel.WriteRow([]interface{}{
            stat.Username,
            stat.Total,
            stat.Completed,
            stat.Pending,
        })
    }
    excel.AutoWidth(4)

    // Sheet 3: All Tasks
    excel.AddSheet("All Tasks")
    excel.WriteHeader([]string{"ID", "User", "Title", "Status", "Created At"})

    tasks, _ := h.taskRepo.FindAll()
    for _, task := range tasks {
        excel.WriteRow([]interface{}{
            task.ID,
            task.User.Username,
            task.Title,
            task.Status,
            task.CreatedAt.Format("2006-01-02"),
        })
    }
    excel.AutoWidth(5)

    buffer, _ := excel.GetBuffer()
    c.Header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    c.Header("Content-Disposition", "attachment; filename=monthly_report.xlsx")
    c.Data(http.StatusOK, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", buffer.Bytes())
}
```

---

## 3️⃣ MID-SENIOR LEVEL - PDF Export

### Install gofpdf

```bash
go get github.com/jung-kurt/gofpdf
```

### PDF Service

```go
// internal/services/pdf_service.go
package services

import (
    "bytes"
    "fmt"

    "github.com/jung-kurt/gofpdf"
)

type PDFService struct {
    pdf *gofpdf.Fpdf
}

func NewPDFService() *PDFService {
    pdf := gofpdf.New("P", "mm", "A4", "")
    pdf.SetMargins(15, 15, 15)
    pdf.SetAutoPageBreak(true, 15)
    pdf.AddPage()

    return &PDFService{pdf: pdf}
}

func (s *PDFService) SetFont(family string, style string, size float64) {
    s.pdf.SetFont(family, style, size)
}

func (s *PDFService) AddTitle(text string) {
    s.pdf.SetFont("Arial", "B", 20)
    s.pdf.SetTextColor(0, 0, 0)
    s.pdf.CellFormat(0, 15, text, "", 1, "C", false, 0, "")
    s.pdf.Ln(5)
}

func (s *PDFService) AddSubtitle(text string) {
    s.pdf.SetFont("Arial", "", 12)
    s.pdf.SetTextColor(100, 100, 100)
    s.pdf.CellFormat(0, 8, text, "", 1, "C", false, 0, "")
    s.pdf.Ln(5)
}

func (s *PDFService) AddParagraph(text string) {
    s.pdf.SetFont("Arial", "", 11)
    s.pdf.SetTextColor(0, 0, 0)
    s.pdf.MultiCell(0, 6, text, "", "", false)
    s.pdf.Ln(3)
}

func (s *PDFService) AddTable(headers []string, data [][]string, widths []float64) {
    // Header
    s.pdf.SetFont("Arial", "B", 10)
    s.pdf.SetFillColor(68, 114, 196)
    s.pdf.SetTextColor(255, 255, 255)

    for i, header := range headers {
        s.pdf.CellFormat(widths[i], 10, header, "1", 0, "C", true, 0, "")
    }
    s.pdf.Ln(-1)

    // Data
    s.pdf.SetFont("Arial", "", 10)
    s.pdf.SetTextColor(0, 0, 0)

    fill := false
    for _, row := range data {
        if fill {
            s.pdf.SetFillColor(240, 240, 240)
        } else {
            s.pdf.SetFillColor(255, 255, 255)
        }

        for i, cell := range row {
            s.pdf.CellFormat(widths[i], 8, cell, "1", 0, "", true, 0, "")
        }
        s.pdf.Ln(-1)
        fill = !fill
    }
    s.pdf.Ln(5)
}

func (s *PDFService) AddLine() {
    s.pdf.Line(15, s.pdf.GetY(), 195, s.pdf.GetY())
    s.pdf.Ln(5)
}

func (s *PDFService) AddSpacer(height float64) {
    s.pdf.Ln(height)
}

func (s *PDFService) GetBuffer() (*bytes.Buffer, error) {
    var buffer bytes.Buffer
    err := s.pdf.Output(&buffer)
    return &buffer, err
}

func (s *PDFService) SaveToFile(path string) error {
    return s.pdf.OutputFileAndClose(path)
}
```

### Invoice PDF

```go
// internal/services/invoice_service.go
package services

import (
    "fmt"
    "time"

    "myapp/internal/models"
)

type InvoiceService struct{}

func NewInvoiceService() *InvoiceService {
    return &InvoiceService{}
}

func (s *InvoiceService) GenerateInvoice(invoice *models.Invoice) (*PDFService, error) {
    pdf := NewPDFService()

    // Header
    pdf.AddTitle("INVOICE")
    pdf.AddSubtitle(fmt.Sprintf("Invoice #%s", invoice.Number))

    pdf.AddSpacer(10)

    // From/To info
    pdf.SetFont("Arial", "", 10)
    pdf.pdf.SetXY(15, pdf.pdf.GetY())
    pdf.pdf.MultiCell(85, 5, fmt.Sprintf(
        "From:\n%s\n%s\n%s",
        "Your Company Name",
        "123 Business Street",
        "billing@company.com",
    ), "", "", false)

    pdf.pdf.SetXY(110, pdf.pdf.GetY()-25)
    pdf.pdf.MultiCell(85, 5, fmt.Sprintf(
        "Bill To:\n%s\n%s\n%s",
        invoice.Customer.Name,
        invoice.Customer.Address,
        invoice.Customer.Email,
    ), "", "", false)

    pdf.AddSpacer(15)

    // Invoice details
    pdf.pdf.SetFont("Arial", "", 10)
    pdf.pdf.CellFormat(0, 6, fmt.Sprintf("Invoice Date: %s", invoice.CreatedAt.Format("January 02, 2006")), "", 1, "", false, 0, "")
    pdf.pdf.CellFormat(0, 6, fmt.Sprintf("Due Date: %s", invoice.DueDate.Format("January 02, 2006")), "", 1, "", false, 0, "")

    pdf.AddSpacer(10)

    // Items table
    headers := []string{"Description", "Qty", "Unit Price", "Total"}
    widths := []float64{80, 20, 35, 35}

    var data [][]string
    for _, item := range invoice.Items {
        data = append(data, []string{
            item.Description,
            fmt.Sprintf("%d", item.Quantity),
            fmt.Sprintf("$%.2f", item.UnitPrice),
            fmt.Sprintf("$%.2f", item.Total),
        })
    }

    pdf.AddTable(headers, data, widths)

    // Totals
    pdf.pdf.SetFont("Arial", "", 10)
    pdf.pdf.SetX(130)
    pdf.pdf.CellFormat(35, 7, "Subtotal:", "1", 0, "R", false, 0, "")
    pdf.pdf.CellFormat(35, 7, fmt.Sprintf("$%.2f", invoice.Subtotal), "1", 1, "R", false, 0, "")

    pdf.pdf.SetX(130)
    pdf.pdf.CellFormat(35, 7, fmt.Sprintf("Tax (%.0f%%):", invoice.TaxRate), "1", 0, "R", false, 0, "")
    pdf.pdf.CellFormat(35, 7, fmt.Sprintf("$%.2f", invoice.TaxAmount), "1", 1, "R", false, 0, "")

    pdf.pdf.SetFont("Arial", "B", 11)
    pdf.pdf.SetFillColor(68, 114, 196)
    pdf.pdf.SetTextColor(255, 255, 255)
    pdf.pdf.SetX(130)
    pdf.pdf.CellFormat(35, 8, "Total:", "1", 0, "R", true, 0, "")
    pdf.pdf.CellFormat(35, 8, fmt.Sprintf("$%.2f", invoice.Total), "1", 1, "R", true, 0, "")

    // Footer
    pdf.AddSpacer(20)
    pdf.pdf.SetTextColor(0, 0, 0)
    pdf.pdf.SetFont("Arial", "", 10)
    pdf.pdf.MultiCell(0, 5, "Payment Terms: Net 30 days\nBank: Bank Name - Account: 1234567890\n\nThank you for your business!", "", "C", false)

    return pdf, nil
}
```

### Invoice Handler

```go
// internal/handlers/export.go
func (h *ExportHandler) ExportInvoicePDF(c *gin.Context) {
    invoiceID := c.Param("id")

    invoice, err := h.invoiceRepo.FindByID(invoiceID)
    if err != nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "Invoice not found"})
        return
    }

    invoiceService := services.NewInvoiceService()
    pdf, err := invoiceService.GenerateInvoice(invoice)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate PDF"})
        return
    }

    buffer, err := pdf.GetBuffer()
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate PDF"})
        return
    }

    filename := fmt.Sprintf("invoice_%s.pdf", invoice.Number)
    c.Header("Content-Type", "application/pdf")
    c.Header("Content-Disposition", fmt.Sprintf("attachment; filename=%s", filename))
    c.Data(http.StatusOK, "application/pdf", buffer.Bytes())
}
```

---

## 4️⃣ SENIOR LEVEL - Background Export untuk Large Data

### Export Job Model

```go
// internal/models/export_job.go
package models

import (
    "time"

    "gorm.io/datatypes"
    "gorm.io/gorm"
)

type ExportStatus string

const (
    ExportStatusPending    ExportStatus = "pending"
    ExportStatusProcessing ExportStatus = "processing"
    ExportStatusCompleted  ExportStatus = "completed"
    ExportStatusFailed     ExportStatus = "failed"
)

type ExportJob struct {
    gorm.Model
    UserID       uint           `gorm:"index"`
    ExportType   string         // tasks, users, report
    Format       string         // csv, excel, pdf
    Filters      datatypes.JSON
    Status       ExportStatus   `gorm:"index"`
    Progress     int            // 0-100
    FilePath     string
    ErrorMessage string
    CompletedAt  *time.Time
}
```

### Background Export Worker

```go
// internal/workers/export_worker.go
package workers

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "time"

    "myapp/internal/models"
    "myapp/internal/repositories"
    "myapp/internal/services"
)

type ExportWorker struct {
    jobRepo  *repositories.ExportJobRepository
    taskRepo *repositories.TaskRepository
    jobs     chan uint
}

func NewExportWorker(jobRepo *repositories.ExportJobRepository, taskRepo *repositories.TaskRepository) *ExportWorker {
    return &ExportWorker{
        jobRepo:  jobRepo,
        taskRepo: taskRepo,
        jobs:     make(chan uint, 100),
    }
}

func (w *ExportWorker) Start(ctx context.Context, workers int) {
    for i := 0; i < workers; i++ {
        go w.worker(ctx, i)
    }
    log.Printf("Started %d export workers", workers)
}

func (w *ExportWorker) Enqueue(jobID uint) {
    w.jobs <- jobID
}

func (w *ExportWorker) worker(ctx context.Context, id int) {
    for {
        select {
        case <-ctx.Done():
            return
        case jobID := <-w.jobs:
            w.processJob(jobID)
        }
    }
}

func (w *ExportWorker) processJob(jobID uint) {
    job, err := w.jobRepo.FindByID(jobID)
    if err != nil {
        log.Printf("Job %d not found: %v", jobID, err)
        return
    }

    // Update status
    job.Status = models.ExportStatusProcessing
    w.jobRepo.Update(job)

    var exportErr error

    switch job.ExportType {
    case "tasks":
        exportErr = w.exportTasks(job)
    default:
        exportErr = fmt.Errorf("unknown export type: %s", job.ExportType)
    }

    if exportErr != nil {
        job.Status = models.ExportStatusFailed
        job.ErrorMessage = exportErr.Error()
    } else {
        job.Status = models.ExportStatusCompleted
        now := time.Now()
        job.CompletedAt = &now
        job.Progress = 100
    }

    w.jobRepo.Update(job)
}

func (w *ExportWorker) exportTasks(job *models.ExportJob) error {
    // Parse filters
    var filters repositories.TaskFilter
    json.Unmarshal(job.Filters, &filters)
    filters.UserID = job.UserID

    // Get total count for progress
    total, _ := w.taskRepo.CountWithFilter(filters)

    // Create Excel
    excel := services.NewExcelService("Tasks")
    excel.WriteHeader([]string{"ID", "Title", "Status", "Created At"})

    // Process in batches
    batchSize := 1000
    offset := 0
    processed := 0

    for {
        tasks, err := w.taskRepo.FindWithFilterPaginated(filters, batchSize, offset)
        if err != nil {
            return err
        }

        if len(tasks) == 0 {
            break
        }

        for _, task := range tasks {
            excel.WriteRow([]interface{}{
                task.ID,
                task.Title,
                task.Status,
                task.CreatedAt.Format("2006-01-02"),
            })
            processed++
        }

        // Update progress
        job.Progress = int(float64(processed) / float64(total) * 100)
        w.jobRepo.Update(job)

        offset += batchSize
    }

    // Save file
    filePath := fmt.Sprintf("exports/export_%d.xlsx", job.ID)
    if err := excel.SaveToFile(filePath); err != nil {
        return err
    }

    job.FilePath = filePath
    return nil
}
```

### Export API Handler

```go
// internal/handlers/export.go
func (h *ExportHandler) CreateExportJob(c *gin.Context) {
    var req struct {
        ExportType string                 `json:"export_type" binding:"required"`
        Format     string                 `json:"format"`
        Filters    map[string]interface{} `json:"filters"`
    }

    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    userID := c.GetUint("user_id")
    filtersJSON, _ := json.Marshal(req.Filters)

    job := &models.ExportJob{
        UserID:     userID,
        ExportType: req.ExportType,
        Format:     req.Format,
        Filters:    filtersJSON,
        Status:     models.ExportStatusPending,
    }

    if err := h.jobRepo.Create(job); err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create job"})
        return
    }

    // Enqueue job
    h.exportWorker.Enqueue(job.ID)

    c.JSON(http.StatusAccepted, gin.H{
        "job_id":  job.ID,
        "status":  "pending",
        "message": "Export job created. You will be notified when ready.",
    })
}

func (h *ExportHandler) GetExportJobStatus(c *gin.Context) {
    jobID := c.Param("id")

    job, err := h.jobRepo.FindByID(jobID)
    if err != nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "Job not found"})
        return
    }

    response := gin.H{
        "job_id":   job.ID,
        "status":   job.Status,
        "progress": job.Progress,
    }

    if job.Status == models.ExportStatusCompleted {
        response["download_url"] = fmt.Sprintf("/api/exports/%d/download", job.ID)
    }

    if job.Status == models.ExportStatusFailed {
        response["error"] = job.ErrorMessage
    }

    c.JSON(http.StatusOK, response)
}

func (h *ExportHandler) DownloadExport(c *gin.Context) {
    jobID := c.Param("id")
    userID := c.GetUint("user_id")

    job, err := h.jobRepo.FindByID(jobID)
    if err != nil || job.UserID != userID {
        c.JSON(http.StatusNotFound, gin.H{"error": "Job not found"})
        return
    }

    if job.Status != models.ExportStatusCompleted {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Export not ready"})
        return
    }

    c.File(job.FilePath)
}
```

---

## 📋 Quick Reference

### Export Format Comparison

| Format | Best For | Library |
|--------|----------|---------|
| **CSV** | Simple data, large files | Built-in `encoding/csv` |
| **Excel** | Formatted reports | `excelize` |
| **PDF** | Invoices, formal docs | `gofpdf` |

### Export Checklist

```
□ Add proper headers
□ Handle large datasets with batching
□ Use goroutines for big exports
□ Set proper Content-Type
□ Add progress tracking
□ Cleanup old export files
□ Log all export activities
```

---

## 🔗 Related Docs

- [CONCURRENCY.md](CONCURRENCY.md) - Goroutines for async export
- [FILE_UPLOAD.md](FILE_UPLOAD.md) - Store export files
