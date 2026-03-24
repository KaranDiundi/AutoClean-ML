import { create } from "zustand";
import type { Dataset } from "./types";

interface AppState {
  datasets: Dataset[];
  selectedDataset: Dataset | null;
  setDatasets: (datasets: Dataset[]) => void;
  addDataset: (dataset: Dataset) => void;
  removeDataset: (id: string) => void;
  setSelectedDataset: (dataset: Dataset | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  datasets: [],
  selectedDataset: null,
  setDatasets: (datasets) => set({ datasets }),
  addDataset: (dataset) => set((state) => ({ datasets: [dataset, ...state.datasets] })),
  removeDataset: (id) =>
    set((state) => ({
      datasets: state.datasets.filter((d) => d.id !== id),
      selectedDataset: state.selectedDataset?.id === id ? null : state.selectedDataset,
    })),
  setSelectedDataset: (dataset) => set({ selectedDataset: dataset }),
}));
