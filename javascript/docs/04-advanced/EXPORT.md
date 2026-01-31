# 📊 EXPORT - Express.js (Junior → Senior)

Dokumentasi lengkap tentang export data ke berbagai format: CSV, Excel, dan PDF.

---

## 🎯 Kapan Butuh Export?

```
Use Cases:
✅ Export laporan (PDF)
✅ Download data user (CSV/Excel)
✅ Generate invoice (PDF)
✅ Backup data (CSV)
✅ Analytics reports (Excel)
```

---

## 1️⃣ JUNIOR LEVEL - CSV Export

### Simple CSV Export

```javascript
// src/controllers/export.controller.js
const prisma = require('../lib/prisma');

exports.exportTasksCSV = async (req, res) => {
  try {
    const tasks = await prisma.task.findMany({
      where: { userId: req.user.id },
      orderBy: { createdAt: 'desc' }
    });

    // Set headers
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename=tasks.csv');

    // Write CSV header
    res.write('ID,Title,Description,Status,Priority,Created At\n');

    // Write data
    for (const task of tasks) {
      const row = [
        task.id,
        `"${task.title.replace(/"/g, '""')}"`, // Escape quotes
        `"${(task.description || '').replace(/"/g, '""')}"`,
        task.status,
        task.priority,
        task.createdAt.toISOString()
      ].join(',');
      
      res.write(row + '\n');
    }

    res.end();
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
```

### CSV dengan Library

```bash
npm install csv-stringify
```

```javascript
// src/services/csv.service.js
const { stringify } = require('csv-stringify');

class CSVService {
  async generate(data, columns) {
    return new Promise((resolve, reject) => {
      stringify(data, {
        header: true,
        columns
      }, (err, output) => {
        if (err) reject(err);
        else resolve(output);
      });
    });
  }

  streamToResponse(data, columns, res, filename) {
    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    res.setHeader('Content-Disposition', `attachment; filename=${filename}`);
    
    // Write BOM for Excel compatibility
    res.write('\ufeff');

    const stringifier = stringify({
      header: true,
      columns
    });

    stringifier.pipe(res);

    for (const row of data) {
      stringifier.write(row);
    }

    stringifier.end();
  }
}

module.exports = new CSVService();
```

### Usage

```javascript
// src/controllers/export.controller.js
const csvService = require('../services/csv.service');

exports.exportTasksCSV = async (req, res) => {
  try {
    const { status, priority, dateFrom, dateTo } = req.query;

    const where = { userId: req.user.id };
    if (status) where.status = status;
    if (priority) where.priority = priority;
    if (dateFrom || dateTo) {
      where.createdAt = {};
      if (dateFrom) where.createdAt.gte = new Date(dateFrom);
      if (dateTo) where.createdAt.lte = new Date(dateTo);
    }

    const tasks = await prisma.task.findMany({ where });

    const columns = [
      { key: 'id', header: 'ID' },
      { key: 'title', header: 'Title' },
      { key: 'description', header: 'Description' },
      { key: 'status', header: 'Status' },
      { key: 'priority', header: 'Priority' },
      { key: 'createdAt', header: 'Created At' }
    ];

    const data = tasks.map(task => ({
      ...task,
      createdAt: task.createdAt.toISOString()
    }));

    csvService.streamToResponse(data, columns, res, 'tasks_export.csv');
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
```

---

## 2️⃣ MID LEVEL - Excel Export

### Install ExcelJS

```bash
npm install exceljs
```

### Excel Service

```javascript
// src/services/excel.service.js
const ExcelJS = require('exceljs');

class ExcelService {
  constructor() {
    this.workbook = null;
    this.worksheet = null;
  }

  createWorkbook() {
    this.workbook = new ExcelJS.Workbook();
    this.workbook.creator = 'YourApp';
    this.workbook.created = new Date();
    return this;
  }

  addSheet(name) {
    this.worksheet = this.workbook.addWorksheet(name);
    return this;
  }

  setColumns(columns) {
    this.worksheet.columns = columns.map(col => ({
      header: col.header,
      key: col.key,
      width: col.width || 15
    }));

    // Style header
    this.worksheet.getRow(1).font = { bold: true, color: { argb: 'FFFFFFFF' } };
    this.worksheet.getRow(1).fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FF4472C4' }
    };
    this.worksheet.getRow(1).alignment = { horizontal: 'center' };

    return this;
  }

  addRows(data) {
    data.forEach((row, index) => {
      this.worksheet.addRow(row);
      
      // Alternate row colors
      if (index % 2 === 1) {
        this.worksheet.getRow(index + 2).fill = {
          type: 'pattern',
          pattern: 'solid',
          fgColor: { argb: 'FFF2F2F2' }
        };
      }
    });

    // Add borders
    this.worksheet.eachRow((row, rowNumber) => {
      row.eachCell((cell) => {
        cell.border = {
          top: { style: 'thin' },
          left: { style: 'thin' },
          bottom: { style: 'thin' },
          right: { style: 'thin' }
        };
      });
    });

    return this;
  }

  async getBuffer() {
    return this.workbook.xlsx.writeBuffer();
  }

  async writeToResponse(res, filename) {
    res.setHeader(
      'Content-Type',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    );
    res.setHeader('Content-Disposition', `attachment; filename=${filename}`);

    await this.workbook.xlsx.write(res);
    res.end();
  }

  async saveToFile(filepath) {
    await this.workbook.xlsx.writeFile(filepath);
  }
}

module.exports = ExcelService;
```

### Export Handler

```javascript
// src/controllers/export.controller.js
const ExcelService = require('../services/excel.service');

exports.exportTasksExcel = async (req, res) => {
  try {
    const tasks = await prisma.task.findMany({
      where: { userId: req.user.id },
      orderBy: { createdAt: 'desc' }
    });

    const excel = new ExcelService();
    
    excel
      .createWorkbook()
      .addSheet('Tasks')
      .setColumns([
        { header: 'ID', key: 'id', width: 10 },
        { header: 'Title', key: 'title', width: 30 },
        { header: 'Description', key: 'description', width: 40 },
        { header: 'Status', key: 'status', width: 15 },
        { header: 'Priority', key: 'priority', width: 15 },
        { header: 'Created At', key: 'createdAt', width: 20 }
      ])
      .addRows(tasks.map(task => ({
        ...task,
        createdAt: task.createdAt.toISOString().split('T')[0]
      })));

    await excel.writeToResponse(res, 'tasks_export.xlsx');
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
```

### Multi-Sheet Report

```javascript
exports.exportMonthlyReport = async (req, res) => {
  try {
    const excel = new ExcelService();
    excel.createWorkbook();

    // Sheet 1: Summary
    excel.addSheet('Summary');
    excel.setColumns([
      { header: 'Metric', key: 'metric', width: 25 },
      { header: 'Value', key: 'value', width: 15 }
    ]);

    const totalUsers = await prisma.user.count();
    const totalTasks = await prisma.task.count();
    const completedTasks = await prisma.task.count({ where: { status: 'done' } });

    excel.addRows([
      { metric: 'Total Users', value: totalUsers },
      { metric: 'Total Tasks', value: totalTasks },
      { metric: 'Completed Tasks', value: completedTasks },
      { metric: 'Completion Rate', value: `${((completedTasks / totalTasks) * 100).toFixed(1)}%` }
    ]);

    // Sheet 2: Tasks by User
    excel.addSheet('Tasks by User');
    excel.setColumns([
      { header: 'User', key: 'user', width: 25 },
      { header: 'Total', key: 'total', width: 10 },
      { header: 'Completed', key: 'completed', width: 12 },
      { header: 'Pending', key: 'pending', width: 10 }
    ]);

    const userStats = await prisma.user.findMany({
      include: {
        _count: {
          select: { tasks: true }
        },
        tasks: {
          select: { status: true }
        }
      }
    });

    excel.addRows(userStats.map(user => ({
      user: user.name,
      total: user._count.tasks,
      completed: user.tasks.filter(t => t.status === 'done').length,
      pending: user.tasks.filter(t => t.status === 'pending').length
    })));

    // Sheet 3: All Tasks
    excel.addSheet('All Tasks');
    excel.setColumns([
      { header: 'ID', key: 'id', width: 10 },
      { header: 'User', key: 'user', width: 20 },
      { header: 'Title', key: 'title', width: 30 },
      { header: 'Status', key: 'status', width: 12 },
      { header: 'Created', key: 'createdAt', width: 15 }
    ]);

    const allTasks = await prisma.task.findMany({
      include: { user: { select: { name: true } } }
    });

    excel.addRows(allTasks.map(task => ({
      id: task.id,
      user: task.user.name,
      title: task.title,
      status: task.status,
      createdAt: task.createdAt.toISOString().split('T')[0]
    })));

    await excel.writeToResponse(res, 'monthly_report.xlsx');
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
```

---

## 3️⃣ MID-SENIOR LEVEL - PDF Export

### Install PDFKit

```bash
npm install pdfkit
```

### PDF Service

```javascript
// src/services/pdf.service.js
const PDFDocument = require('pdfkit');

class PDFService {
  constructor() {
    this.doc = new PDFDocument({
      size: 'A4',
      margins: { top: 50, bottom: 50, left: 50, right: 50 }
    });
    this.y = 50;
  }

  pipe(stream) {
    this.doc.pipe(stream);
    return this;
  }

  addTitle(text) {
    this.doc
      .fontSize(24)
      .fillColor('#333333')
      .text(text, { align: 'center' });
    this.y = this.doc.y + 20;
    return this;
  }

  addSubtitle(text) {
    this.doc
      .fontSize(12)
      .fillColor('#666666')
      .text(text, { align: 'center' });
    this.y = this.doc.y + 20;
    return this;
  }

  addParagraph(text) {
    this.doc
      .fontSize(11)
      .fillColor('#333333')
      .text(text, { align: 'left' });
    this.y = this.doc.y + 10;
    return this;
  }

  addSpacer(height = 20) {
    this.doc.moveDown(height / 12);
    this.y += height;
    return this;
  }

  addLine() {
    this.doc
      .strokeColor('#cccccc')
      .lineWidth(1)
      .moveTo(50, this.doc.y)
      .lineTo(545, this.doc.y)
      .stroke();
    this.y = this.doc.y + 10;
    return this;
  }

  addTable(headers, data, options = {}) {
    const {
      columnWidths = headers.map(() => (495 / headers.length)),
      headerBackground = '#4472C4',
      headerColor = '#FFFFFF',
      rowHeight = 25
    } = options;

    let x = 50;
    const startY = this.doc.y;

    // Draw header
    this.doc
      .fillColor(headerBackground)
      .rect(x, startY, 495, rowHeight)
      .fill();

    this.doc
      .fillColor(headerColor)
      .fontSize(10)
      .font('Helvetica-Bold');

    headers.forEach((header, i) => {
      this.doc.text(header, x + 5, startY + 7, {
        width: columnWidths[i] - 10,
        align: 'left'
      });
      x += columnWidths[i];
    });

    // Draw data rows
    let currentY = startY + rowHeight;
    this.doc.font('Helvetica').fontSize(10);

    data.forEach((row, rowIndex) => {
      x = 50;
      
      // Alternate row background
      if (rowIndex % 2 === 1) {
        this.doc
          .fillColor('#F2F2F2')
          .rect(x, currentY, 495, rowHeight)
          .fill();
      }

      // Draw cell borders
      this.doc
        .strokeColor('#CCCCCC')
        .lineWidth(0.5)
        .rect(x, currentY, 495, rowHeight)
        .stroke();

      this.doc.fillColor('#333333');

      row.forEach((cell, i) => {
        this.doc.text(String(cell || ''), x + 5, currentY + 7, {
          width: columnWidths[i] - 10,
          align: 'left'
        });
        x += columnWidths[i];
      });

      currentY += rowHeight;

      // Add new page if needed
      if (currentY > 750) {
        this.doc.addPage();
        currentY = 50;
      }
    });

    this.doc.y = currentY + 10;
    return this;
  }

  end() {
    this.doc.end();
  }
}

module.exports = PDFService;
```

### Invoice PDF

```javascript
// src/services/invoice.service.js
const PDFDocument = require('pdfkit');

class InvoiceService {
  generateInvoice(invoice, res) {
    const doc = new PDFDocument({ size: 'A4', margin: 50 });
    
    doc.pipe(res);

    // Header
    doc
      .fontSize(28)
      .fillColor('#4472C4')
      .text('INVOICE', 50, 50, { align: 'right' });

    doc
      .fontSize(10)
      .fillColor('#666666')
      .text(`Invoice #: ${invoice.number}`, { align: 'right' })
      .text(`Date: ${invoice.createdAt.toLocaleDateString()}`, { align: 'right' })
      .text(`Due: ${invoice.dueDate.toLocaleDateString()}`, { align: 'right' });

    // Company info
    doc
      .fontSize(12)
      .fillColor('#333333')
      .text('Your Company Name', 50, 50)
      .fontSize(10)
      .text('123 Business Street')
      .text('City, Country 12345')
      .text('billing@company.com');

    // Customer info
    doc
      .text('Bill To:', 50, 160)
      .font('Helvetica-Bold')
      .text(invoice.customer.name)
      .font('Helvetica')
      .text(invoice.customer.address)
      .text(invoice.customer.email);

    // Items table
    const tableTop = 280;
    const tableHeaders = ['Description', 'Qty', 'Unit Price', 'Total'];
    const columnWidths = [250, 50, 80, 80];

    // Header row
    doc
      .fillColor('#4472C4')
      .rect(50, tableTop, 495, 25)
      .fill();

    doc
      .fillColor('#FFFFFF')
      .font('Helvetica-Bold')
      .fontSize(10);

    let x = 55;
    tableHeaders.forEach((header, i) => {
      doc.text(header, x, tableTop + 8);
      x += columnWidths[i];
    });

    // Data rows
    let y = tableTop + 25;
    doc.font('Helvetica').fillColor('#333333');

    invoice.items.forEach((item, index) => {
      if (index % 2 === 1) {
        doc.fillColor('#F9F9F9').rect(50, y, 495, 25).fill();
      }

      doc.fillColor('#333333');
      x = 55;
      
      doc.text(item.description, x, y + 8, { width: 240 });
      x += columnWidths[0];
      doc.text(String(item.quantity), x, y + 8);
      x += columnWidths[1];
      doc.text(`$${item.unitPrice.toFixed(2)}`, x, y + 8);
      x += columnWidths[2];
      doc.text(`$${item.total.toFixed(2)}`, x, y + 8);

      y += 25;
    });

    // Totals
    y += 20;
    doc.font('Helvetica');
    
    const totalsX = 400;
    doc.text('Subtotal:', totalsX, y);
    doc.text(`$${invoice.subtotal.toFixed(2)}`, totalsX + 70, y, { align: 'right', width: 75 });
    
    y += 20;
    doc.text(`Tax (${invoice.taxRate}%):`, totalsX, y);
    doc.text(`$${invoice.taxAmount.toFixed(2)}`, totalsX + 70, y, { align: 'right', width: 75 });
    
    y += 25;
    doc
      .font('Helvetica-Bold')
      .fontSize(12)
      .fillColor('#4472C4')
      .text('Total:', totalsX, y);
    doc.text(`$${invoice.total.toFixed(2)}`, totalsX + 70, y, { align: 'right', width: 75 });

    // Footer
    doc
      .fontSize(10)
      .fillColor('#666666')
      .font('Helvetica')
      .text('Payment Terms: Net 30 days', 50, 700)
      .text('Thank you for your business!', 50, 715);

    doc.end();
  }
}

module.exports = new InvoiceService();
```

### Invoice Handler

```javascript
// src/controllers/export.controller.js
const invoiceService = require('../services/invoice.service');

exports.exportInvoicePDF = async (req, res) => {
  try {
    const invoice = await prisma.invoice.findUnique({
      where: { id: req.params.id },
      include: {
        customer: true,
        items: true
      }
    });

    if (!invoice) {
      return res.status(404).json({ error: 'Invoice not found' });
    }

    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader(
      'Content-Disposition',
      `attachment; filename=invoice_${invoice.number}.pdf`
    );

    invoiceService.generateInvoice(invoice, res);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
```

---

## 4️⃣ SENIOR LEVEL - Puppeteer untuk Complex PDF

### Install Puppeteer

```bash
npm install puppeteer
```

### HTML to PDF Service

```javascript
// src/services/puppeteerPdf.service.js
const puppeteer = require('puppeteer');
const handlebars = require('handlebars');
const fs = require('fs').promises;
const path = require('path');

class PuppeteerPDFService {
  async generateFromTemplate(templateName, data, options = {}) {
    const {
      format = 'A4',
      landscape = false,
      margin = { top: '1cm', right: '1cm', bottom: '1cm', left: '1cm' }
    } = options;

    // Load and compile template
    const templatePath = path.join(__dirname, '../templates/pdf', `${templateName}.hbs`);
    const templateSource = await fs.readFile(templatePath, 'utf8');
    const template = handlebars.compile(templateSource);
    const html = template(data);

    // Launch browser
    const browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
      const page = await browser.newPage();
      await page.setContent(html, { waitUntil: 'networkidle0' });

      const pdf = await page.pdf({
        format,
        landscape,
        margin,
        printBackground: true
      });

      return pdf;
    } finally {
      await browser.close();
    }
  }

  async generateFromURL(url, options = {}) {
    const browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox']
    });

    try {
      const page = await browser.newPage();
      await page.goto(url, { waitUntil: 'networkidle0' });

      return page.pdf({
        format: options.format || 'A4',
        printBackground: true,
        ...options
      });
    } finally {
      await browser.close();
    }
  }
}

module.exports = new PuppeteerPDFService();
```

### Usage

```javascript
// src/controllers/export.controller.js
const puppeteerPdfService = require('../services/puppeteerPdf.service');

exports.exportReportPDF = async (req, res) => {
  try {
    const data = await getReportData(req.user.id);

    const pdf = await puppeteerPdfService.generateFromTemplate('report', {
      ...data,
      generatedAt: new Date().toLocaleString()
    });

    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', 'attachment; filename=report.pdf');
    res.send(pdf);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
```

---

## 5️⃣ EXPERT LEVEL - Background Export dengan Queue

### Export Job Model (Prisma)

```prisma
model ExportJob {
  id          String   @id @default(uuid())
  userId      String
  exportType  String   // tasks, users, report
  format      String   // csv, excel, pdf
  filters     Json?
  status      ExportStatus @default(PENDING)
  progress    Int      @default(0)
  filePath    String?
  errorMessage String?
  createdAt   DateTime @default(now())
  completedAt DateTime?

  user        User     @relation(fields: [userId], references: [id])

  @@index([userId, status])
}

enum ExportStatus {
  PENDING
  PROCESSING
  COMPLETED
  FAILED
}
```

### Export Queue

```javascript
// src/queues/export.queue.js
const { Queue, Worker } = require('bullmq');
const prisma = require('../lib/prisma');
const ExcelService = require('../services/excel.service');
const path = require('path');
const fs = require('fs').promises;

const connection = {
  host: process.env.REDIS_HOST,
  port: parseInt(process.env.REDIS_PORT)
};

const exportQueue = new Queue('export', { connection });

const exportWorker = new Worker('export', async (job) => {
  const { jobId } = job.data;

  const exportJob = await prisma.exportJob.findUnique({
    where: { id: jobId }
  });

  if (!exportJob) throw new Error('Export job not found');

  // Update status
  await prisma.exportJob.update({
    where: { id: jobId },
    data: { status: 'PROCESSING' }
  });

  try {
    let filePath;

    switch (exportJob.exportType) {
      case 'tasks':
        filePath = await exportTasks(exportJob);
        break;
      default:
        throw new Error(`Unknown export type: ${exportJob.exportType}`);
    }

    await prisma.exportJob.update({
      where: { id: jobId },
      data: {
        status: 'COMPLETED',
        filePath,
        progress: 100,
        completedAt: new Date()
      }
    });

    // TODO: Send notification email
    
  } catch (error) {
    await prisma.exportJob.update({
      where: { id: jobId },
      data: {
        status: 'FAILED',
        errorMessage: error.message
      }
    });
    throw error;
  }
}, { connection, concurrency: 2 });

async function exportTasks(exportJob) {
  const filters = exportJob.filters || {};
  
  const where = { userId: exportJob.userId, ...filters };
  const total = await prisma.task.count({ where });
  
  const tasks = await prisma.task.findMany({
    where,
    orderBy: { createdAt: 'desc' }
  });

  const excel = new ExcelService();
  excel
    .createWorkbook()
    .addSheet('Tasks')
    .setColumns([
      { header: 'ID', key: 'id', width: 10 },
      { header: 'Title', key: 'title', width: 30 },
      { header: 'Status', key: 'status', width: 12 },
      { header: 'Created At', key: 'createdAt', width: 15 }
    ])
    .addRows(tasks.map(t => ({
      ...t,
      createdAt: t.createdAt.toISOString().split('T')[0]
    })));

  const filename = `export_${exportJob.id}.xlsx`;
  const filePath = path.join('exports', filename);
  
  await fs.mkdir('exports', { recursive: true });
  await excel.saveToFile(filePath);

  return filePath;
}

const queueExport = async (userId, exportType, format, filters = {}) => {
  const exportJob = await prisma.exportJob.create({
    data: {
      userId,
      exportType,
      format,
      filters
    }
  });

  await exportQueue.add('process', { jobId: exportJob.id });

  return exportJob;
};

module.exports = {
  exportQueue,
  exportWorker,
  queueExport
};
```

### Export API

```javascript
// src/controllers/export.controller.js
const { queueExport } = require('../queues/export.queue');

exports.createExportJob = async (req, res) => {
  try {
    const { exportType, format, filters } = req.body;

    const job = await queueExport(
      req.user.id,
      exportType,
      format || 'excel',
      filters
    );

    res.status(202).json({
      jobId: job.id,
      status: 'pending',
      message: 'Export job created. You will be notified when ready.'
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

exports.getExportJobStatus = async (req, res) => {
  try {
    const job = await prisma.exportJob.findUnique({
      where: { id: req.params.id }
    });

    if (!job || job.userId !== req.user.id) {
      return res.status(404).json({ error: 'Job not found' });
    }

    const response = {
      jobId: job.id,
      status: job.status,
      progress: job.progress
    };

    if (job.status === 'COMPLETED') {
      response.downloadUrl = `/api/exports/${job.id}/download`;
    }

    if (job.status === 'FAILED') {
      response.error = job.errorMessage;
    }

    res.json(response);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

exports.downloadExport = async (req, res) => {
  try {
    const job = await prisma.exportJob.findUnique({
      where: { id: req.params.id }
    });

    if (!job || job.userId !== req.user.id) {
      return res.status(404).json({ error: 'Job not found' });
    }

    if (job.status !== 'COMPLETED') {
      return res.status(400).json({ error: 'Export not ready' });
    }

    res.download(job.filePath);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
```

---

## 📋 Quick Reference

### Export Format Comparison

| Format | Best For | Library |
|--------|----------|---------|
| **CSV** | Simple data, large files | `csv-stringify` |
| **Excel** | Formatted reports | `exceljs` |
| **PDF** | Invoices, formal docs | `pdfkit`, `puppeteer` |

### Export Checklist

```
□ Add proper headers
□ Handle large datasets with streaming
□ Use background jobs for big exports
□ Set proper Content-Type
□ Add progress tracking
□ Cleanup old export files
□ Log all export activities
□ Send notification when complete
```

---

## 🔗 Related Docs

- [REDIS.md](REDIS.md) - Queue for async exports
- [FILE_UPLOAD.md](FILE_UPLOAD.md) - Store export files
- [EMAIL.md](EMAIL.md) - Send export notifications
