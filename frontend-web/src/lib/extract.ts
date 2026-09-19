// Client-side text extraction so the free backend never has to do heavy OCR.
// PDFs: read embedded text with pdf.js; if a scan (little/no text), render pages
// and OCR them. Images: OCR directly. All in the browser (Tesseract.js).
import * as pdfjsLib from "pdfjs-dist";
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import { createWorker } from "tesseract.js";

pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl;

export type Progress = (pct: number, label: string) => void;

export interface Extracted {
  text: string;
  method: "pdf-text" | "pdf-ocr" | "image-ocr";
}

function isPdf(f: File) {
  return f.type.includes("pdf") || /\.pdf$/i.test(f.name);
}
function isImage(f: File) {
  return f.type.startsWith("image/") || /\.(png|jpe?g|webp|bmp|tiff?|gif|heic)$/i.test(f.name);
}
/** true if this file type is extracted in the browser (image or PDF). */
export function isClientExtractable(f: File) {
  return isPdf(f) || isImage(f);
}

async function ocr(sources: (HTMLCanvasElement | File | Blob)[], onProgress?: Progress): Promise<string> {
  const worker = await createWorker("eng", 1, {
    logger: (m: { status: string; progress: number }) => {
      if (m.status === "recognizing text") onProgress?.(m.progress, "Reading text");
    },
  });
  try {
    const parts: string[] = [];
    for (let i = 0; i < sources.length; i++) {
      if (sources.length > 1) onProgress?.(i / sources.length, `Reading page ${i + 1} of ${sources.length}`);
      const { data } = await worker.recognize(sources[i]);
      parts.push(data.text || "");
    }
    return parts.join("\n");
  } finally {
    await worker.terminate();
  }
}

async function extractPdf(file: File, onProgress?: Progress): Promise<Extracted> {
  const data = new Uint8Array(await file.arrayBuffer());
  const pdf = await pdfjsLib.getDocument({ data }).promise;
  // 1) try embedded text
  let text = "";
  for (let p = 1; p <= pdf.numPages; p++) {
    const page = await pdf.getPage(p);
    const content = await page.getTextContent();
    text += content.items.map((it: any) => ("str" in it ? it.str : "")).join(" ") + "\n";
  }
  if (text.trim().length >= 40) return { text, method: "pdf-text" };

  // 2) scanned PDF -> render pages and OCR (cap pages to keep it responsive)
  const maxPages = Math.min(pdf.numPages, 5);
  const canvases: HTMLCanvasElement[] = [];
  for (let p = 1; p <= maxPages; p++) {
    const page = await pdf.getPage(p);
    const viewport = page.getViewport({ scale: 2 });
    const canvas = document.createElement("canvas");
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    const ctx = canvas.getContext("2d")!;
    await page.render({ canvasContext: ctx, viewport } as any).promise;
    canvases.push(canvas);
  }
  const ocrText = await ocr(canvases, onProgress);
  return { text: ocrText, method: "pdf-ocr" };
}

/**
 * Extract text in the browser. Returns null for types handled by the server
 * (DOCX / TXT), so the caller can send those to the API instead.
 */
export async function extractText(file: File, onProgress?: Progress): Promise<Extracted | null> {
  if (isPdf(file)) return extractPdf(file, onProgress);
  if (isImage(file)) {
    onProgress?.(0, "Reading text");
    const text = await ocr([file], onProgress);
    return { text, method: "image-ocr" };
  }
  return null; // docx / txt -> server
}
