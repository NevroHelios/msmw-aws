"use client";

import Image from "next/image";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">
            MSME Retail Intelligence
          </h1>
          <p className="text-xl text-purple-200">
            Upload CSV files for instant data extraction
          </p>
        </div>

        {/* Upload Card */}
        <div className="max-w-2xl mx-auto bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl border border-white/20 p-8">
          <h2 className="text-2xl font-semibold text-white mb-6">
            📊 Upload Sales or Inventory CSV
          </h2>

          <UploadForm />

          {/* Info */}
          <div className="mt-8 p-4 bg-blue-500/20 border border-blue-400/30 rounded-lg">
            <p className="text-sm text-blue-100">
              <strong>✨ Supported:</strong> CSV files (sales, inventory)<br />
              <strong>🔒 Secure:</strong> Processed on AWS Lambda<br />
              <strong>💰 Cost:</strong> FREE tier (1M requests/month)
            </p>
          </div>
        </div>

        {/* Sample Files */}
        <div className="max-w-2xl mx-auto mt-8 text-center">
          <p className="text-purple-200 mb-4">📁 Try our sample files:</p>
          <div className="flex gap-4 justify-center flex-wrap">
            <a
              href="/samples/sample_sales.csv"
              download
              className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium hover:from-purple-600 hover:to-pink-600 transition-all shadow-lg hover:shadow-xl"
            >
              📈 Sample Sales
            </a>
            <a
              href="/samples/sample_inventory.csv"
              download
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg font-medium hover:from-blue-600 hover:to-cyan-600 transition-all shadow-lg hover:shadow-xl"
            >
              📦 Sample Inventory
            </a>
          </div>
        </div>

        {/* API Status */}
        <div className="max-w-2xl mx-auto mt-12 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-500/20 border border-green-400/30 rounded-full">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-green-100 text-sm font-medium">Backend Live</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function UploadForm() {
  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        const form = e.currentTarget;
        const formData = new FormData(form);
        const file = formData.get('file') as File;
        const storeId = formData.get('store_id') as string;

        if (!file) {
          alert('Please select a file');
          return;
        }

        // Show loading
        const button = form.querySelector('button[type="submit"]') as HTMLButtonElement;
        const originalText = button.textContent;
        button.textContent = '⏳ Uploading...';
        button.disabled = true;

        try {
          // Convert file to base64
          const reader = new FileReader();
          reader.readAsDataURL(file);

          await new Promise((resolve) => {
            reader.onload = resolve;
          });

          const base64 = (reader.result as string).split(',')[1];

          // Auto-detect file type based on filename and extension
          let fileType = 'sales_csv'; // default
          const fileName = file.name.toLowerCase();

          if (fileName.endsWith('.csv')) {
            fileType = fileName.includes('inventory') ? 'inventory_csv' : 'sales_csv';
          } else if (fileName.match(/\.(jpg|jpeg|png)$/)) {
            fileType = fileName.includes('receipt') ? 'receipt_image' : 'invoice_image';
          }

          // Call API
          const response = await fetch('https://pf5prjt91j.execute-api.ap-south-1.amazonaws.com/dev/upload', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              store_id: storeId,
              file_type: fileType,
              file_name: file.name,
              file_content: base64,
            }),
          });

          const data = await response.json();

          if (response.ok) {
            alert(`✅ Upload successful!\n\nUpload ID: ${data.upload_id}\n\nThe file is being processed. Check DynamoDB for extracted data.`);
            form.reset();
          } else {
            alert(`❌ Upload failed: ${data.message || 'Unknown error'}`);
          }
        } catch (error) {
          alert(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        } finally {
          button.textContent = originalText;
          button.disabled = false;
        }
      }}
      className="space-y-6"
    >
      {/* Store Selection */}
      <div>
        <label htmlFor="store_id" className="block text-sm font-medium text-purple-200 mb-2">
          Select Store
        </label>
        <select
          id="store_id"
          name="store_id"
          required
          className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option value="STORE001">Sharma Kirana Store (Chennai)</option>
          <option value="STORE002">Patel General Store (Ahmedabad)</option>
          <option value="STORE003">Kumar Retail Mart (Bangalore)</option>
        </select>
      </div>

      {/* File Upload */}
      <div>
        <label htmlFor="file" className="block text-sm font-medium text-purple-200 mb-2">
          Choose File (CSV or Image)
        </label>
        <input
          type="file"
          id="file"
          name="file"
          accept=".csv,.jpg,.jpeg,.png"
          required
          className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-purple-500 file:text-white hover:file:bg-purple-600 file:cursor-pointer"
        />
        <p className="text-xs text-purple-300 mt-2">
          📄 CSV: sales.csv, inventory.csv | 🖼️ Images: invoice.jpg, receipt.png
        </p>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        className="w-full px-6 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold text-lg hover:from-purple-600 hover:to-pink-600 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
      >
        🚀 Upload & Extract Data
      </button>
    </form>
  );
}
