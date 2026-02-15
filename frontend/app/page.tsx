"use client";

import { useState } from "react";

const API_BASE = "https://pf5prjt91j.execute-api.ap-south-1.amazonaws.com/dev";

const STORES = [
  { id: "STORE001", name: "Sharma Kirana Store (Chennai)" },
  { id: "STORE002", name: "Patel General Store (Ahmedabad)" },
  { id: "STORE003", name: "Kumar Retail Mart (Bangalore)" },
];

interface UploadRecord {
  upload_id: string;
  file_type: string;
  status: string;
  uploaded_at: string;
  file_name: string;
  file_size_mb: number;
}

interface ExtractedRecord {
  record_id: string;
  type: string;
  extraction_method: string;
  extracted_at: string;
  data: any;
}

interface StoreData {
  store_id: string;
  uploads: UploadRecord[];
  extracted_data: ExtractedRecord[];
  total_uploads: number;
  total_records: number;
}

export default function Home() {
  const [storeData, setStoreData] = useState<StoreData | null>(null);
  const [loadingData, setLoadingData] = useState(false);
  const [selectedStore, setSelectedStore] = useState("STORE001");

  const fetchStoreData = async (storeId: string) => {
    setLoadingData(true);
    try {
      const res = await fetch(`${API_BASE}/data/${storeId}`);
      const data = await res.json();
      if (res.ok) {
        setStoreData(data);
      } else {
        alert(`❌ Failed to load data: ${data.error || "Unknown error"}`);
      }
    } catch (err) {
      alert(`❌ Error: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setLoadingData(false);
    }
  };

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

          <UploadForm
            onUploadSuccess={(storeId) => fetchStoreData(storeId)}
          />

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

        {/* ===== Data Viewer ===== */}
        <div className="max-w-4xl mx-auto mt-12 bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl border border-white/20 p-8">
          <h2 className="text-2xl font-semibold text-white mb-6">
            📋 View Extracted Data
          </h2>
          <div className="flex gap-4 items-end flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-purple-200 mb-2">
                Select Store
              </label>
              <select
                value={selectedStore}
                onChange={(e) => setSelectedStore(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                {STORES.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={() => fetchStoreData(selectedStore)}
              disabled={loadingData}
              className="px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-lg font-semibold hover:from-emerald-600 hover:to-teal-600 transition-all shadow-lg hover:shadow-xl disabled:opacity-50"
            >
              {loadingData ? "⏳ Loading..." : "🔍 Fetch Data"}
            </button>
          </div>

          {storeData && (
            <div className="mt-8 space-y-6">
              {/* Stats */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-purple-500/20 border border-purple-400/30 rounded-lg text-center">
                  <div className="text-3xl font-bold text-white">{storeData.total_uploads}</div>
                  <div className="text-sm text-purple-200">Uploads</div>
                </div>
                <div className="p-4 bg-emerald-500/20 border border-emerald-400/30 rounded-lg text-center">
                  <div className="text-3xl font-bold text-white">{storeData.total_records}</div>
                  <div className="text-sm text-emerald-200">Extracted Records</div>
                </div>
              </div>

              {/* Upload History */}
              {storeData.uploads.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-white mb-3">📤 Upload History</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                      <thead className="text-purple-200 border-b border-white/20">
                        <tr>
                          <th className="px-3 py-2">File</th>
                          <th className="px-3 py-2">Type</th>
                          <th className="px-3 py-2">Status</th>
                          <th className="px-3 py-2">Date</th>
                        </tr>
                      </thead>
                      <tbody className="text-white/80">
                        {storeData.uploads.map((u) => (
                          <tr key={u.upload_id} className="border-b border-white/5 hover:bg-white/5">
                            <td className="px-3 py-2 font-mono text-xs">{u.file_name || u.upload_id}</td>
                            <td className="px-3 py-2">
                              <span className="px-2 py-0.5 rounded-full text-xs bg-blue-500/30 text-blue-200">
                                {u.file_type}
                              </span>
                            </td>
                            <td className="px-3 py-2">
                              <span
                                className={`px-2 py-0.5 rounded-full text-xs ${u.status === "EXTRACTED"
                                    ? "bg-green-500/30 text-green-200"
                                    : u.status === "FAILED"
                                      ? "bg-red-500/30 text-red-200"
                                      : "bg-yellow-500/30 text-yellow-200"
                                  }`}
                              >
                                {u.status}
                              </span>
                            </td>
                            <td className="px-3 py-2 text-xs text-white/60">
                              {u.uploaded_at ? new Date(u.uploaded_at).toLocaleString() : "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Extracted Data */}
              {storeData.extracted_data.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-white mb-3">📊 Extracted Data</h3>
                  <div className="space-y-4">
                    {storeData.extracted_data.map((record) => (
                      <div
                        key={record.record_id}
                        className="bg-white/5 border border-white/10 rounded-lg p-4"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <span className="px-2 py-0.5 rounded-full text-xs bg-emerald-500/30 text-emerald-200 font-semibold">
                              {record.type}
                            </span>
                            <span className="text-xs text-white/50">
                              {record.extraction_method}
                            </span>
                          </div>
                          <span className="text-xs text-white/40">
                            {record.extracted_at ? new Date(record.extracted_at).toLocaleString() : ""}
                          </span>
                        </div>

                        {/* Render data based on type */}
                        {record.data?.records ? (
                          <div className="overflow-x-auto">
                            <table className="w-full text-xs text-left">
                              <thead className="text-purple-200 border-b border-white/20">
                                <tr>
                                  {Object.keys(record.data.records[0] || {}).map((key) => (
                                    <th key={key} className="px-2 py-1 capitalize">
                                      {key.replace(/_/g, " ")}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody className="text-white/70">
                                {record.data.records.map((row: any, i: number) => (
                                  <tr key={i} className="border-b border-white/5">
                                    {Object.values(row).map((val: any, j: number) => (
                                      <td key={j} className="px-2 py-1">
                                        {typeof val === "number" ? val.toLocaleString() : String(val)}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                            {record.data.total_amount !== undefined && (
                              <div className="mt-2 text-right text-sm font-semibold text-emerald-300">
                                Total: ₹{Number(record.data.total_amount).toLocaleString()}
                              </div>
                            )}
                          </div>
                        ) : (
                          <pre className="text-xs text-white/60 overflow-x-auto whitespace-pre-wrap">
                            {JSON.stringify(record.data, null, 2)}
                          </pre>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {storeData.extracted_data.length === 0 && storeData.uploads.length === 0 && (
                <div className="text-center py-8 text-white/40">
                  No data found for this store. Upload a CSV to get started!
                </div>
              )}
            </div>
          )}
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

function UploadForm({ onUploadSuccess }: { onUploadSuccess: (storeId: string) => void }) {
  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        const form = e.currentTarget;
        const formData = new FormData(form);
        const file = formData.get("file") as File;
        const storeId = formData.get("store_id") as string;

        if (!file) {
          alert("Please select a file");
          return;
        }

        const button = form.querySelector('button[type="submit"]') as HTMLButtonElement;
        const originalText = button.textContent;
        button.textContent = "⏳ Uploading...";
        button.disabled = true;

        try {
          const reader = new FileReader();
          reader.readAsDataURL(file);

          await new Promise((resolve) => {
            reader.onload = resolve;
          });

          const base64 = (reader.result as string).split(",")[1];

          let fileType = "sales_csv";
          const fileName = file.name.toLowerCase();

          if (fileName.endsWith(".csv")) {
            fileType = fileName.includes("inventory") ? "inventory_csv" : "sales_csv";
          } else if (fileName.match(/\.(jpg|jpeg|png)$/)) {
            fileType = fileName.includes("receipt") ? "receipt_image" : "invoice_image";
          }

          const response = await fetch(`${API_BASE}/upload`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              store_id: storeId,
              file_type: fileType,
              file_name: file.name,
              file_content: base64,
            }),
          });

          const data = await response.json();

          if (response.ok) {
            alert(
              `✅ Upload successful!\n\nUpload ID: ${data.upload_id}\n\nProcessing... click "Fetch Data" to see results.`
            );
            form.reset();
            // Auto-refresh data after a short delay for extraction to complete
            setTimeout(() => onUploadSuccess(storeId), 3000);
          } else {
            alert(`❌ Upload failed: ${data.message || data.error || "Unknown error"}`);
          }
        } catch (error) {
          alert(`❌ Error: ${error instanceof Error ? error.message : "Unknown error"}`);
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
          {STORES.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
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
