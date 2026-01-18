import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Save, Loader2, Sparkles, AlertTriangle } from 'lucide-react';
import {
  createRequest,
  updateRequest,
  getRequest,
  getCommodityGroups,
  classifyCommodity,
} from '../api/client';
import type { OrderLine, CommodityGroup, PdfExtractionResult } from '../types';
import OrderLineEditor from './OrderLineEditor';
import PdfUploader from './PdfUploader';

interface RequestFormProps {
  editMode: boolean;
  requestId?: number;
  onSuccess?: () => void;
}

const currencies = ['EUR', 'USD', 'GBP', 'CHF'];

export default function RequestForm({ editMode, requestId, onSuccess }: RequestFormProps) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(editMode);
  const [classifying, setClassifying] = useState(false);
  const [commodityGroups, setCommodityGroups] = useState<CommodityGroup[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    requestor_name: '',
    title: '',
    vendor_name: '',
    vat_id: '',
    department: '',
    commodity_group_id: '',
    currency: 'EUR',
    stated_total_cost: null as number | null,
  });
  const [orderLines, setOrderLines] = useState<OrderLine[]>([]);

  useEffect(() => {
    getCommodityGroups()
      .then((groups) => {
        setCommodityGroups(groups);
        if (!formData.commodity_group_id && groups.length > 0) {
          setFormData((prev) => ({ ...prev, commodity_group_id: groups[0].id }));
        }
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (editMode && requestId) {
      setLoadingData(true);
      getRequest(requestId)
        .then((request) => {
          setFormData({
            requestor_name: request.requestor_name,
            title: request.title,
            vendor_name: request.vendor_name,
            vat_id: request.vat_id,
            department: request.department,
            commodity_group_id: request.commodity_group_id,
            currency: request.currency,
            stated_total_cost: request.stated_total_cost,
          });
          setOrderLines(request.order_lines);
        })
        .catch((err) => {
          setError('Failed to load request');
          console.error(err);
        })
        .finally(() => setLoadingData(false));
    }
  }, [editMode, requestId]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'stated_total_cost' ? (value ? parseFloat(value) : null) : value,
    }));
  };

  const handlePdfExtracted = async (data: PdfExtractionResult) => {
    setFormData((prev) => ({
      ...prev,
      requestor_name: data.requestor_name || prev.requestor_name,
      title: data.title || prev.title,
      vendor_name: data.vendor_name || prev.vendor_name,
      vat_id: data.vat_id || prev.vat_id,
      department: data.department || prev.department,
      currency: data.currency || prev.currency,
      stated_total_cost: data.stated_total_cost,
    }));
    if (data.order_lines.length > 0) {
      setOrderLines(data.order_lines);
      
      const descriptions = data.order_lines.map((l) => l.description).join(', ');
      if (descriptions.trim()) {
        setClassifying(true);
        try {
          const result = await classifyCommodity(descriptions);
          setFormData((prev) => ({ ...prev, commodity_group_id: result.commodity_group_id }));
        } catch (err) {
          console.error('Auto-classification failed:', err);
        } finally {
          setClassifying(false);
        }
      }
    }
  };

  const handleAutoClassify = async () => {
    const descriptions = orderLines.map((l) => l.description).join(', ');
    if (!descriptions.trim()) {
      setError('Add order lines with descriptions first');
      return;
    }

    setClassifying(true);
    try {
      const result = await classifyCommodity(descriptions);
      setFormData((prev) => ({ ...prev, commodity_group_id: result.commodity_group_id }));
    } catch (err) {
      setError('Failed to classify commodity');
      console.error(err);
    } finally {
      setClassifying(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = {
        ...formData,
        order_lines: orderLines.map(({ id, ...line }) => line),
      };

      if (editMode && requestId) {
        await updateRequest(requestId, payload);
      } else {
        await createRequest(payload);
      }

      if (onSuccess) {
        onSuccess();
      } else {
        navigate('/overview');
      }
    } catch (err) {
      setError('Failed to save request. Please check your input.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  const groupedCommodities = commodityGroups.reduce((acc, group) => {
    if (!acc[group.category]) {
      acc[group.category] = [];
    }
    acc[group.category].push(group);
    return acc;
  }, {} as Record<string, CommodityGroup[]>);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="bg-red-900/20 border border-red-700 text-red-400 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h2 className="text-lg font-medium text-gray-100 mb-4">Request Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Requestor Name *</label>
                <input
                  type="text"
                  name="requestor_name"
                  value={formData.requestor_name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Your name"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Request Title *</label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Brief description of request"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Vendor Name *</label>
                <input
                  type="text"
                  name="vendor_name"
                  value={formData.vendor_name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Supplier company name"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">VAT ID</label>
                <input
                  type="text"
                  name="vat_id"
                  value={formData.vat_id}
                  onChange={handleChange}
                  pattern="DE\d{9}"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="DE123456789"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Department *</label>
                <input
                  type="text"
                  name="department"
                  value={formData.department}
                  onChange={handleChange}
                  required
                  placeholder="Enter department"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Currency *</label>
                <select
                  name="currency"
                  value={formData.currency}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {currencies.map((curr) => (
                    <option key={curr} value={curr}>
                      {curr}
                    </option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm text-gray-400 mb-1">Commodity Group *</label>
                <div className="flex gap-2">
                  <select
                    name="commodity_group_id"
                    value={formData.commodity_group_id}
                    onChange={handleChange}
                    required
                    className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {Object.entries(groupedCommodities).map(([category, groups]) => (
                      <optgroup key={category} label={category}>
                        {groups.map((group) => (
                          <option key={group.id} value={group.id}>
                            {group.id} - {group.name}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={handleAutoClassify}
                    disabled={classifying}
                    className="flex items-center gap-2 px-3 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 rounded-lg transition-colors"
                    title="Auto-classify based on order lines"
                  >
                    {classifying ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Sparkles className="h-4 w-4" />
                    )}
                    <span className="hidden sm:inline">Auto</span>
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Stated Total Cost</label>
                <input
                  type="number"
                  name="stated_total_cost"
                  value={formData.stated_total_cost ?? ''}
                  onChange={handleChange}
                  step="0.01"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="As stated in document"
                />
                {formData.stated_total_cost !== null && (() => {
                  const calculatedTotal = orderLines.reduce((sum, line) => sum + line.unit_price * line.quantity, 0);
                  const hasMismatch = Math.abs(calculatedTotal - formData.stated_total_cost) > 0.01;
                  return hasMismatch ? (
                    <div className="flex items-center gap-2 text-yellow-400 text-sm mt-2">
                      <AlertTriangle className="h-4 w-4" />
                      <span>
                        Mismatch: stated {formData.stated_total_cost.toFixed(2)} vs calculated {calculatedTotal.toFixed(2)} {formData.currency}
                      </span>
                    </div>
                  ) : null;
                })()}
              </div>
            </div>
          </div>

          <OrderLineEditor
            orderLines={orderLines}
            onChange={setOrderLines}
            currency={formData.currency}
            showMismatch={true}
          />
        </div>

        <div className="space-y-6">
          <PdfUploader onExtracted={handlePdfExtracted} />

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium text-lg transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-5 w-5" />
                {editMode ? 'Update Request' : 'Create Request'}
              </>
            )}
          </button>
        </div>
      </div>
    </form>
  );
}
