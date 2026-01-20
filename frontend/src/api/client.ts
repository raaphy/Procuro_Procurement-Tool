import axios from 'axios';
import type {
  ProcurementRequest,
  CommodityGroup,
  CreateRequestPayload,
  UpdateRequestPayload,
  PdfExtractionResult,
  ClassificationRequest,
  ClassificationResponse,
} from '../types';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function getRequests(status?: string): Promise<ProcurementRequest[]> {
  const params = status ? { status } : {};
  const response = await api.get<ProcurementRequest[]>('/requests', { params });
  return response.data;
}

export async function getRequest(id: number): Promise<ProcurementRequest> {
  const response = await api.get<ProcurementRequest>(`/requests/${id}`);
  return response.data;
}

export async function createRequest(data: CreateRequestPayload): Promise<ProcurementRequest> {
  const response = await api.post<ProcurementRequest>('/requests', data);
  return response.data;
}

export async function updateRequest(id: number, data: UpdateRequestPayload): Promise<ProcurementRequest> {
  const response = await api.put<ProcurementRequest>(`/requests/${id}`, data);
  return response.data;
}

export async function updateStatus(id: number, status: string): Promise<ProcurementRequest> {
  const response = await api.patch<ProcurementRequest>(`/requests/${id}/status`, { status });
  return response.data;
}

export async function deleteRequest(id: number): Promise<void> {
  await api.delete(`/requests/${id}`);
}

export async function extractPdf(file: File): Promise<PdfExtractionResult> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post<PdfExtractionResult>('/extraction/pdf', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

export async function classifyCommodity(data: ClassificationRequest): Promise<ClassificationResponse> {
  const response = await api.post<ClassificationResponse>('/extraction/classify-commodity', data);
  return response.data;
}

export async function getCommodityGroups(): Promise<CommodityGroup[]> {
  const response = await api.get<CommodityGroup[]>('/commodity-groups');
  return response.data;
}

export async function uploadPdf(requestId: number, file: File): Promise<void> {
  const formData = new FormData();
  formData.append('file', file);
  await api.post(`/requests/${requestId}/pdf`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

export async function deletePdf(requestId: number): Promise<void> {
  await api.delete(`/requests/${requestId}/pdf`);
}

export default api;
