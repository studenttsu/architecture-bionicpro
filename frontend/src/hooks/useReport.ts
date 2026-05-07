import { useState, useMemo } from 'react';
import { useKeycloak } from '@react-keycloak/web';
import { defineAbilityFor, AppAbility } from '../ability';

export interface ReportRecord {
  user_id: string;
  report_date: string;
  username: string;
  email: string;
  prosthesis_id: string;
  avg_reaction_time_ms: number;
  total_movements: number;
  avg_battery_level: number;
  signal_quality_avg: number;
  active_hours: number;
  anomaly_count: number;
  last_calibration_date: string;
  etl_processed_at: string;
}

export interface ReportResponse {
  user_id: string;
  username: string;
  date_from: string;
  date_to: string;
  last_processed_date: string;
  total_records: number;
  reports: ReportRecord[];
}

interface UseReportReturn {
  loading: boolean;
  error: string | null;
  reportData: ReportResponse | null;
  ability: AppAbility;
  username: string | undefined;
  fetchReport: () => Promise<void>;
  exportAsJson: () => void;
}

export function useReport(): UseReportReturn {
  const { keycloak } = useKeycloak();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportData, setReportData] = useState<ReportResponse | null>(null);

  const ability = useMemo(() => {
    const roles: string[] = keycloak?.tokenParsed?.realm_access?.roles ?? [];
    return defineAbilityFor(roles);
  }, [keycloak?.tokenParsed]);

  const username = keycloak?.tokenParsed?.preferred_username;

  const fetchReport = async () => {
    if (!keycloak?.token) {
      setError('Not authenticated');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      setReportData(null);

      const response = await fetch(process.env.REACT_APP_API_URL + '/reports', {
        headers: { 'Authorization': 'Bearer ' + keycloak.token },
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => null);
        throw new Error(errorBody?.detail || 'Server error: ' + response.status);
      }

      setReportData(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const exportAsJson = () => {
    if (!reportData) return;
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'report_' + reportData.user_id + '_' + reportData.date_to + '.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  return { loading, error, reportData, ability, username, fetchReport, exportAsJson };
}
