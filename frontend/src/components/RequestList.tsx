import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ChevronDown,
  ChevronUp,
  Edit,
  Trash2,
  AlertTriangle,
  Loader2,
  Search,
} from 'lucide-react';
import { getRequests, updateStatus, deleteRequest, getCommodityGroups } from '../api/client';
import type { ProcurementRequest, CommodityGroup } from '../types';

const statusColors = {
  Open: 'bg-yellow-600',
  'In Progress': 'bg-blue-600',
  Closed: 'bg-green-600',
};

const statusOptions = ['Open', 'In Progress', 'Closed'] as const;

export default function RequestList() {
  const [requests, setRequests] = useState<ProcurementRequest[]>([]);
  const [commodityGroups, setCommodityGroups] = useState<CommodityGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState<number | null>(null);

  const getCommodityDisplay = (id: string) => {
    const group = commodityGroups.find((g) => g.id === id);
    return group ? `${id} - ${group.category} - ${group.name}` : id;
  };

  const loadRequests = async () => {
    setLoading(true);
    try {
      const [data, groups] = await Promise.all([
        getRequests(statusFilter || undefined),
        getCommodityGroups(),
      ]);
      setRequests(data);
      setCommodityGroups(groups);
    } catch (err) {
      console.error('Failed to load requests:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRequests();
  }, [statusFilter]);

  const handleStatusChange = async (id: number, newStatus: string) => {
    setUpdatingStatus(id);
    try {
      const updated = await updateStatus(id, newStatus);
      setRequests((prev) =>
        prev.map((r) => (r.id === id ? updated : r))
      );
    } catch (err) {
      console.error('Failed to update status:', err);
    } finally {
      setUpdatingStatus(null);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this request?')) return;

    try {
      await deleteRequest(id);
      setRequests((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      console.error('Failed to delete request:', err);
    }
  };

  const filteredRequests = requests.filter((r) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      r.title.toLowerCase().includes(query) ||
      r.vendor_name.toLowerCase().includes(query) ||
      r.requestor_name.toLowerCase().includes(query)
    );
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search requests..."
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">All Statuses</option>
          {statusOptions.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </div>

      {filteredRequests.length === 0 ? (
        <div className="text-center py-12 text-gray-400 bg-gray-800 rounded-lg border border-gray-700">
          No requests found.
        </div>
      ) : (
        <div className="space-y-3">
          {filteredRequests.map((request) => (
            <div
              key={request.id}
              className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden"
            >
              <div
                className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-750"
                onClick={() =>
                  setExpandedId(expandedId === request.id ? null : request.id)
                }
              >
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      statusColors[request.status]
                    }`}
                  >
                    {request.status}
                  </span>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-gray-100 truncate">
                        {request.title}
                      </h3>
                      {request.has_total_mismatch && (
                        <AlertTriangle className="h-4 w-4 text-yellow-500 flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-sm text-gray-400 truncate">
                      {request.vendor_name} • {request.department}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right hidden sm:block">
                    <div className="font-medium text-gray-100">
                      {request.calculated_total_cost.toFixed(2)} {request.currency}
                    </div>
                    <div className="text-xs text-gray-400">
                      {request.order_lines.length} items
                    </div>
                  </div>
                  {expandedId === request.id ? (
                    <ChevronUp className="h-5 w-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-gray-400" />
                  )}
                </div>
              </div>

              {expandedId === request.id && (
                <div className="border-t border-gray-700 p-4 bg-gray-850">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <span className="text-xs text-gray-400">Requestor</span>
                      <p className="text-gray-100">{request.requestor_name}</p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400">Vendor</span>
                      <p className="text-gray-100">{request.vendor_name}</p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400">VAT ID</span>
                      <p className="text-gray-100">{request.vat_id || '-'}</p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400">Department</span>
                      <p className="text-gray-100">{request.department}</p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400">Commodity</span>
                      <p className="text-gray-100">{getCommodityDisplay(request.commodity_group_id)}</p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400">Currency</span>
                      <p className="text-gray-100">{request.currency}</p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400">Created</span>
                      <p className="text-gray-100">
                        {new Date(request.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400">Updated</span>
                      <p className="text-gray-100">
                        {request.updated_at ? new Date(request.updated_at).toLocaleDateString() : '-'}
                      </p>
                    </div>
                  </div>

                  {request.status_history && request.status_history.length > 0 && (
                    <div className="mb-4">
                      <span className="text-xs text-gray-400 block mb-2">Status History</span>
                      <div className="bg-gray-900 rounded-lg p-3 space-y-1 text-sm">
                        {request.status_history.map((h, idx) => (
                          <div key={idx} className="text-gray-300">
                            {new Date(h.changed_at).toLocaleString()} — {h.from_status || 'Created'} → {h.to_status} (by {h.changed_by})
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {request.order_lines.length > 0 && (
                    <div className="mb-4">
                      <span className="text-xs text-gray-400 block mb-2">Order Lines</span>
                      <div className="bg-gray-900 rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-800">
                            <tr>
                              <th className="text-left px-3 py-2 text-gray-400">Description</th>
                              <th className="text-right px-3 py-2 text-gray-400">Qty</th>
                              <th className="text-right px-3 py-2 text-gray-400">Unit Price</th>
                              <th className="text-right px-3 py-2 text-gray-400">Total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {request.order_lines.map((line, idx) => (
                              <tr key={idx} className="border-t border-gray-800">
                                <td className="px-3 py-2 text-gray-100">{line.description}</td>
                                <td className="px-3 py-2 text-gray-100 text-right">
                                  {line.quantity} {line.unit}
                                </td>
                                <td className="px-3 py-2 text-gray-100 text-right">
                                  {line.unit_price.toFixed(2)}
                                </td>
                                <td className="px-3 py-2 text-gray-100 text-right">
                                  {(line.unit_price * line.quantity).toFixed(2)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {request.has_total_mismatch && (
                    <div className="mb-4 flex items-center gap-2 text-yellow-500 bg-yellow-900/20 px-3 py-2 rounded-lg text-sm">
                      <AlertTriangle className="h-4 w-4" />
                      Total mismatch: Stated {request.stated_total_cost?.toFixed(2)} vs
                      Calculated {request.calculated_total_cost.toFixed(2)} {request.currency}
                    </div>
                  )}

                  <div className="flex items-center justify-between gap-4 pt-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-400">Status:</span>
                      <select
                        value={request.status}
                        onChange={(e) => handleStatusChange(request.id, e.target.value)}
                        disabled={updatingStatus === request.id}
                        className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-gray-100 text-sm focus:ring-2 focus:ring-blue-500"
                      >
                        {statusOptions.map((status) => (
                          <option key={status} value={status}>
                            {status}
                          </option>
                        ))}
                      </select>
                      {updatingStatus === request.id && (
                        <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Link
                        to={`/edit/${request.id}`}
                        className="flex items-center gap-1 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm transition-colors"
                      >
                        <Edit className="h-4 w-4" />
                        Edit
                      </Link>
                      <button
                        onClick={() => handleDelete(request.id)}
                        className="flex items-center gap-1 px-3 py-1.5 bg-red-900/30 hover:bg-red-900/50 text-red-400 rounded text-sm transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
