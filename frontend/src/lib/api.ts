const API_BASE = "";

export interface User {
  id: number;
  username: string;
  email: string;
  thumb: string | null;
}

export interface AuthStatusResponse {
  authenticated: boolean;
  user?: User;
  isAdmin?: boolean;
}

export interface PinResponse {
  pin_id: number;
  code: string;
  auth_url: string;
}

export interface CheckPinResponse {
  authenticated: boolean;
  user?: User;
  session_token?: string;
  cookie_name?: string;
  max_age?: number;
  error?: string;
}

export interface MediaItem {
  request: {
    id: number;
    request_id: number;
    type: string;
    media_id: number;
    tmdb_id?: number | null;
    requested_by?: string;
    requested_at?: string;
    status: string;
    extended?: boolean;
  };
  media: {
    id: number;
    title: string;
    poster: string | null;
    seasons: number[] | null;
    size_on_disk: number | null;
    available_since: string | null;
    available: boolean;
  };
  retention: {
    days_left: number;
    delete: boolean;
    remind: boolean;
    extended?: boolean;
    deletion_date?: string;
  };
}

export interface MediaListResponse {
  media: MediaItem[];
  count: number;
  overseerr_url?: string | null;
}

/**
 * Check current authentication status
 */
export async function getAuthStatus(): Promise<AuthStatusResponse> {
  const response = await fetch(`${API_BASE}/auth/status`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Failed to check auth status");
  }
  return response.json();
}

/**
 * Create a new Plex PIN for authentication
 */
export async function createPin(): Promise<PinResponse> {
  const response = await fetch(`${API_BASE}/auth/pin`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Failed to create Plex PIN");
  }
  return response.json();
}

/**
 * Check if a PIN has been claimed
 */
export async function checkPin(pinId: number): Promise<CheckPinResponse> {
  const response = await fetch(`${API_BASE}/auth/check-pin?pin_id=${pinId}`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Failed to check PIN");
  }
  return response.json();
}

/**
 * Log out the current user
 */
export async function logout(): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Failed to logout");
  }
}

/**
 * Request a time extension for a media request
 */
export async function requestExtend(requestId: number): Promise<{
  status: string;
  request_id: number;
}> {
  const response = await fetch(`${API_BASE}/api/requests/${requestId}/extend`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    if (response.status === 401) throw new Error("Unauthorized");
    if (response.status === 404) throw new Error("Request not found");
    if (response.status === 409) throw new Error("Request has already been extended");
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail ?? "Failed to request extension");
  }
  return response.json();
}

/**
 * Get the media list
 */
export async function getMediaList(): Promise<MediaListResponse> {
  const response = await fetch(`${API_BASE}/api/media`, {
    credentials: "include",
  });
  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Unauthorized");
    }
    throw new Error("Failed to fetch media list");
  }
  return response.json();
}

// --- Admin Schedules ---

export interface Schedule {
  id: number;
  job_type: "check" | "process";
  cron_expression: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface ScheduleCreate {
  job_type: "check" | "process";
  cron_expression: string;
  enabled?: boolean;
}

export interface ScheduleUpdate {
  job_type?: "check" | "process";
  cron_expression?: string;
  enabled?: boolean;
}

export async function getSchedules(): Promise<Schedule[]> {
  const response = await fetch(`${API_BASE}/api/admin/schedules`, {
    credentials: "include",
  });
  if (!response.ok) {
    if (response.status === 401) throw new Error("Unauthorized");
    if (response.status === 403) throw new Error("Forbidden");
    throw new Error("Failed to fetch schedules");
  }
  return response.json();
}

export async function createSchedule(body: ScheduleCreate): Promise<Schedule> {
  const response = await fetch(`${API_BASE}/api/admin/schedules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    if (response.status === 401) throw new Error("Unauthorized");
    if (response.status === 403) throw new Error("Forbidden");
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail ?? "Failed to create schedule");
  }
  return response.json();
}

export async function updateSchedule(
  id: number,
  body: ScheduleUpdate
): Promise<Schedule> {
  const response = await fetch(`${API_BASE}/api/admin/schedules/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    if (response.status === 401) throw new Error("Unauthorized");
    if (response.status === 403) throw new Error("Forbidden");
    if (response.status === 404) throw new Error("Schedule not found");
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail ?? "Failed to update schedule");
  }
  return response.json();
}

export async function deleteSchedule(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/api/admin/schedules/${id}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!response.ok) {
    if (response.status === 401) throw new Error("Unauthorized");
    if (response.status === 403) throw new Error("Forbidden");
    if (response.status === 404) throw new Error("Schedule not found");
    throw new Error("Failed to delete schedule");
  }
}

export async function runScheduleNow(id: number): Promise<{ status: string; job_type: string }> {
  const response = await fetch(`${API_BASE}/api/admin/schedules/${id}/run`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    if (response.status === 401) throw new Error("Unauthorized");
    if (response.status === 403) throw new Error("Forbidden");
    if (response.status === 404) throw new Error("Schedule not found");
    throw new Error("Failed to run schedule");
  }
  return response.json();
}

// --- Admin Job Runs ---

export interface JobRun {
  id: number;
  job_type: "check" | "process";
  finished_at: string;
  success: boolean;
  error_message: string | null;
}

export async function getJobRuns(): Promise<JobRun[]> {
  const response = await fetch(`${API_BASE}/api/admin/jobs`, {
    credentials: "include",
  });
  if (!response.ok) {
    if (response.status === 401) throw new Error("Unauthorized");
    if (response.status === 403) throw new Error("Forbidden");
    throw new Error("Failed to fetch job runs");
  }
  return response.json();
}

// --- Admin Settings ---

export interface ServiceConfig {
  url: string;
  api_key_set: boolean;
}

export interface ServicesConfig {
  overseerr: ServiceConfig;
  radarr: ServiceConfig;
  sonarr: ServiceConfig;
}

export interface EmailConfig {
  enabled: boolean;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string | null;
  smtp_password_set: boolean;
  smtp_from_email: string;
  smtp_ssl_tls: boolean;
  smtp_starttls: boolean;
}

export interface AdminSettings {
  retention_days: number;
  reminder_days: number;
  extension_days: number;
  services: ServicesConfig;
  notifications: {
    email: EmailConfig;
  };
}

export interface ServiceConfigUpdate {
  url?: string;
  api_key?: string;
}

export interface ServicesUpdate {
  overseerr?: ServiceConfigUpdate;
  radarr?: ServiceConfigUpdate;
  sonarr?: ServiceConfigUpdate;
}

export interface EmailConfigUpdate {
  enabled?: boolean;
  smtp_host?: string;
  smtp_port?: number;
  smtp_username?: string;
  smtp_password?: string;
  smtp_from_email?: string;
  smtp_ssl_tls?: boolean;
  smtp_starttls?: boolean;
}

export interface AdminSettingsUpdate {
  retention_days?: number;
  reminder_days?: number;
  extension_days?: number;
  services?: ServicesUpdate;
  notifications?: {
    email?: EmailConfigUpdate;
  };
}

export async function getAdminSettings(): Promise<AdminSettings> {
  const response = await fetch(`${API_BASE}/api/admin/settings`, {
    credentials: "include",
  });
  if (!response.ok) {
    if (response.status === 401) throw new Error("Unauthorized");
    if (response.status === 403) throw new Error("Forbidden");
    throw new Error("Failed to fetch settings");
  }
  return response.json();
}

export async function updateAdminSettings(
  body: AdminSettingsUpdate
): Promise<AdminSettings> {
  const response = await fetch(`${API_BASE}/api/admin/settings`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    if (response.status === 401) throw new Error("Unauthorized");
    if (response.status === 403) throw new Error("Forbidden");
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail ?? "Failed to update settings");
  }
  return response.json();
}

export async function testServiceConnection(
  service: "overseerr" | "radarr" | "sonarr"
): Promise<{ service: string; status: string; message: string }> {
  const response = await fetch(
    `${API_BASE}/api/admin/settings/services/test/${service}`,
    {
      method: "POST",
      credentials: "include",
    }
  );
  if (!response.ok) {
    if (response.status === 401) throw new Error("Unauthorized");
    if (response.status === 403) throw new Error("Forbidden");
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail ?? "Failed to test connection");
  }
  return response.json();
}
