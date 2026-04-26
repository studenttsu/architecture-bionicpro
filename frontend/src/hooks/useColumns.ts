import { useMemo } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { ReportRecord } from './useReport';

export function useColumns(): ColumnDef<ReportRecord>[] {
  return useMemo<ColumnDef<ReportRecord>[]>(
    () => [
      {
        accessorKey: 'report_date',
        header: 'Date',
      },
      {
        accessorKey: 'prosthesis_id',
        header: 'Prosthesis',
      },
      {
        accessorKey: 'avg_reaction_time_ms',
        header: 'Avg Reaction (ms)',
        cell: ({ getValue }) => (getValue<number>()).toFixed(1),
        meta: { align: 'right' },
      },
      {
        accessorKey: 'total_movements',
        header: 'Movements',
        meta: { align: 'right' },
      },
      {
        accessorKey: 'avg_battery_level',
        header: 'Battery (%)',
        cell: ({ getValue }) => (getValue<number>()).toFixed(1),
        meta: { align: 'right' },
      },
      {
        accessorKey: 'signal_quality_avg',
        header: 'Signal Quality',
        cell: ({ getValue }) => (getValue<number>() * 100).toFixed(0) + '%',
        meta: { align: 'right' },
      },
      {
        accessorKey: 'active_hours',
        header: 'Active Hours',
        cell: ({ getValue }) => (getValue<number>()).toFixed(1),
        meta: { align: 'right' },
      },
      {
        accessorKey: 'anomaly_count',
        header: 'Anomalies',
        meta: { align: 'right' },
      },
    ],
    []
  );
}
