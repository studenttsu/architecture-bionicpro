import React from 'react';
import { useKeycloak } from '@react-keycloak/web';
import { Can } from '@casl/react';
import { useReport } from '../hooks/useReport';

const ReportPage: React.FC = () => {
  const { keycloak, initialized } = useKeycloak();
  const { loading, error, reportData, ability, username, fetchReport, exportAsJson } = useReport();

  if (!initialized) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  if (!keycloak.authenticated) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
        <div className="p-8 bg-white rounded-lg shadow-md text-center">
          <h1 className="text-2xl font-bold mb-4">BionicPRO Reports</h1>
          <p className="mb-6 text-gray-600">Please log in to view your prosthesis reports</p>
          <button
            onClick={() => keycloak.login()}
            className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <div className="w-full max-w-4xl p-8 bg-white rounded-lg shadow-md">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Usage Reports</h1>
          <button
            onClick={() => keycloak.logout()}
            className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
          >
            Logout
          </button>
        </div>

        <div className="mb-6">
          <p className="text-gray-600">
            Logged in as: <strong>{username}</strong>
          </p>
        </div>

        <div className="flex gap-3 mb-6">
          <Can I="view" a="Report" ability={ability}>
            <button
              onClick={fetchReport}
              disabled={loading}
              className={'px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 ' + (loading ? 'opacity-50 cursor-not-allowed' : '')}
            >
              {loading ? 'Generating Report...' : 'Generate Report'}
            </button>
          </Can>

          {reportData && ability.can('view', 'Report') && (
            <button
              onClick={exportAsJson}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              Download JSON
            </button>
          )}
        </div>

        {!ability.can('view', 'Report') && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 text-yellow-800 rounded">
            Access to reports is only available for prosthesis users.
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}

        {reportData && (
          <div className="mt-4">
            <div className="mb-4 p-3 bg-blue-50 rounded text-sm">
              <p><strong>Period:</strong> {reportData.date_from} - {reportData.date_to}</p>
              <p><strong>Last ETL processed date:</strong> {reportData.last_processed_date}</p>
              <p><strong>Total records:</strong> {reportData.total_records}</p>
            </div>

            {reportData.reports.length === 0 ? (
              <p className="text-gray-500">No report data available for the selected period.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border p-2 text-left">Date</th>
                      <th className="border p-2 text-left">Prosthesis</th>
                      <th className="border p-2 text-right">Avg Reaction (ms)</th>
                      <th className="border p-2 text-right">Movements</th>
                      <th className="border p-2 text-right">Battery (%)</th>
                      <th className="border p-2 text-right">Signal Quality</th>
                      <th className="border p-2 text-right">Active Hours</th>
                      <th className="border p-2 text-right">Anomalies</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.reports.map((record, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="border p-2">{record.report_date}</td>
                        <td className="border p-2">{record.prosthesis_id}</td>
                        <td className="border p-2 text-right">{record.avg_reaction_time_ms.toFixed(1)}</td>
                        <td className="border p-2 text-right">{record.total_movements}</td>
                        <td className="border p-2 text-right">{record.avg_battery_level.toFixed(1)}</td>
                        <td className="border p-2 text-right">{(record.signal_quality_avg * 100).toFixed(0)}%</td>
                        <td className="border p-2 text-right">{record.active_hours.toFixed(1)}</td>
                        <td className="border p-2 text-right">{record.anomaly_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPage;