import { apiClient } from "./auth-api";

export interface DailySuggestionSchedule {
  id: string;
  user_id: string;
  cron_expression: string;
  timezone: string;
  last_run_at?: string;
  created_at: string;
  updated_at: string;
}

export interface DailySuggestionScheduleCreate {
  cron_expression: string;
  timezone?: string;
}

export interface DailySuggestionScheduleUpdate {
  cron_expression?: string;
  timezone?: string;
}

class ScheduleAPI {
  private base = "/schedules/daily-suggestions";

  async getSchedule(): Promise<DailySuggestionSchedule | null> {
    try {
      return await apiClient.request<DailySuggestionSchedule | null>(
        `${this.base}/`
      );
    } catch (e) {
      if ((e as { status?: number }).status === 404) {
        return null;
      }
      throw e;
    }
  }

  async createSchedule(
    data: DailySuggestionScheduleCreate
  ): Promise<DailySuggestionSchedule> {
    return await apiClient.request<DailySuggestionSchedule>(`${this.base}/`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateSchedule(
    data: DailySuggestionScheduleUpdate
  ): Promise<DailySuggestionSchedule> {
    return await apiClient.request<DailySuggestionSchedule>(`${this.base}/`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteSchedule(): Promise<void> {
    await apiClient.request<void>(`${this.base}/`, {
      method: "DELETE",
    });
  }
}

export const scheduleApi = new ScheduleAPI();
