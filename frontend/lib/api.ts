/**
 * API Client for ASX Announcements Backend
 *
 * This module provides typed API calls to the FastAPI backend.
 */

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

export const api = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types

export interface Company {
  id: string;
  asx_code: string;
  company_name: string;
  industry: string | null;
  market_cap: number | null;
  last_updated: string;
  created_at: string;
}

export interface Analysis {
  id: string;
  announcement_id: string;
  summary: string | null;
  sentiment: 'bullish' | 'bearish' | 'neutral' | null;
  key_insights: string[] | null;
  llm_model: string | null;
  confidence_score: number | null;
  processing_time_ms: number | null;
  created_at: string;
}

export interface StockData {
  id: string;
  announcement_id: string;
  company_id: string;
  price_at_announcement: number | null;
  price_1h_after: number | null;
  price_1d_after: number | null;
  price_change_pct: number | null;
  volume_at_announcement: number | null;
  market_cap: number | null;
  pe_ratio: number | null;
  performance_1m_pct: number | null;
  performance_3m_pct: number | null;
  performance_6m_pct: number | null;
  fetched_at: string;
}

export interface AnnouncementList {
  id: string;
  company_id: string;
  asx_code: string;
  title: string;
  announcement_date: string;
  pdf_url: string;
  is_price_sensitive: boolean;
  num_pages: number | null;
  file_size_kb: number | null;
  downloaded_at: string | null;
  processed_at: string | null;
  created_at: string;
  sentiment: string | null;
  company: Company | null;
}

export interface AnnouncementDetail extends AnnouncementList {
  pdf_local_path: string | null;
  markdown_path: string | null;
  analysis: Analysis | null;
  stock_data: StockData[] | null;
}

export interface PaginationMetadata {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  metadata: PaginationMetadata;
}

export interface SearchRequest {
  query?: string;
  asx_codes?: string[];
  date_from?: string;
  date_to?: string;
  price_sensitive_only?: boolean;
  sentiment?: 'bullish' | 'bearish' | 'neutral';
  min_market_cap?: number;
  max_market_cap?: number;
  page?: number;
  page_size?: number;
  sort_by?: 'date' | 'asx_code' | 'market_cap';
  sort_order?: 'asc' | 'desc';
}

// API Functions

/**
 * Get paginated list of announcements
 */
export async function getAnnouncements(params: {
  page?: number;
  page_size?: number;
  asx_code?: string;
  price_sensitive_only?: boolean;
  date_from?: string;
  date_to?: string;
  sentiment?: string;
}): Promise<PaginatedResponse<AnnouncementList>> {
  const response = await api.get<PaginatedResponse<AnnouncementList>>('/announcements', {
    params,
  });
  return response.data;
}

/**
 * Get single announcement by ID
 */
export async function getAnnouncement(id: string): Promise<AnnouncementDetail> {
  const response = await api.get<AnnouncementDetail>(`/announcements/${id}`);
  return response.data;
}

/**
 * Advanced search for announcements
 */
export async function searchAnnouncements(
  searchRequest: SearchRequest
): Promise<PaginatedResponse<AnnouncementList>> {
  const response = await api.post<PaginatedResponse<AnnouncementList>>(
    '/announcements/search',
    searchRequest
  );
  return response.data;
}

/**
 * Get list of companies
 */
export async function getCompanies(params: {
  skip?: number;
  limit?: number;
}): Promise<Company[]> {
  const response = await api.get<Company[]>('/companies', { params });
  return response.data;
}

/**
 * Get company by ASX code
 */
export async function getCompany(asxCode: string): Promise<Company> {
  const response = await api.get<Company>(`/companies/${asxCode}`);
  return response.data;
}

/**
 * Get company announcements
 */
export async function getCompanyAnnouncements(
  asxCode: string,
  params: {
    page?: number;
    page_size?: number;
    price_sensitive_only?: boolean;
  }
): Promise<PaginatedResponse<AnnouncementList>> {
  const response = await api.get<PaginatedResponse<AnnouncementList>>(
    `/companies/${asxCode}/announcements`,
    { params }
  );
  return response.data;
}

/**
 * Check API health
 */
export async function checkHealth(): Promise<{
  status: string;
  timestamp: string;
  version: string;
  environment: string;
  database: string;
}> {
  const response = await axios.get(`${API_BASE_URL}/health`);
  return response.data;
}
