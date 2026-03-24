/** Axios API client with typed endpoints. */

import axios from "axios";
import type { Dataset, PipelineRun, PipelineResults } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 30000,
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || "Unknown error";
    return Promise.reject(new Error(msg));
  }
);

// ── Datasets ────────────────────────────────────────────────

export async function uploadDataset(file: File): Promise<Dataset> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<Dataset>("/datasets/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function listDatasets(): Promise<Dataset[]> {
  const { data } = await api.get<{ datasets: Dataset[] }>("/datasets");
  return data.datasets;
}

export async function getDatasetColumns(datasetId: string): Promise<string[]> {
  const { data } = await api.get<{ columns: string[] }>(
    `/datasets/${datasetId}/columns`
  );
  return data.columns;
}

export async function deleteDataset(datasetId: string): Promise<void> {
  await api.delete(`/datasets/${datasetId}`);
}

// ── Pipelines ───────────────────────────────────────────────

export async function triggerPipeline(
  datasetId: string,
  targetColumn: string
): Promise<PipelineRun> {
  const { data } = await api.post<PipelineRun>("/pipelines/run", {
    dataset_id: datasetId,
    target_column: targetColumn,
  });
  return data;
}

export async function getPipelineResults(
  runId: string
): Promise<PipelineResults> {
  const { data } = await api.get<PipelineResults>(`/pipelines/${runId}/results`);
  return data;
}

export function getDownloadUrl(runId: string): string {
  return `${API_URL}/api/v1/pipelines/${runId}/download`;
}

export function createStatusStream(runId: string): EventSource {
  return new EventSource(
    `${API_URL}/api/v1/pipelines/${runId}/status`
  );
}

export default api;
