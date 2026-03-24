/** TypeScript interfaces matching the API schema. */

export interface Dataset {
  id: string;
  filename: string;
  original_name: string;
  file_type: string;
  file_size_bytes: number;
  row_count: number | null;
  column_count: number | null;
  created_at: string;
}

export interface PipelineRun {
  id: string;
  dataset_id: string;
  target_column: string;
  status: string;
  task_type: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  category: string;
  missing_count: number;
  missing_pct: number;
  n_unique: number;
  mean?: number | null;
  std?: number | null;
  min?: number | null;
  max?: number | null;
}

export interface DataProfile {
  n_rows: number;
  n_cols: number;
  total_missing_pct: number;
  columns: ColumnProfile[];
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface ModelResult {
  task_type: string;
  metrics: Record<string, any>;
  feature_importances: FeatureImportance[];
  train_size: number;
  test_size: number;
}

export interface AuditLogEntry {
  id: number;
  phase: string;
  severity: string;
  message: string;
  created_at: string;
}

export interface PipelineResults {
  run: PipelineRun;
  profile: DataProfile | null;
  model_result: ModelResult | null;
  audit_logs: AuditLogEntry[];
}

export type PipelineStatus =
  | "PENDING"
  | "PROFILING"
  | "CLEANING"
  | "ENGINEERING"
  | "TRAINING"
  | "COMPLETED"
  | "FAILED";
