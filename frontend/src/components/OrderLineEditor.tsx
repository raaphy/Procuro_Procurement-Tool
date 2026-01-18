import { Plus, Trash2, AlertTriangle } from 'lucide-react';
import type { OrderLine } from '../types';

interface OrderLineEditorProps {
  orderLines: OrderLine[];
  onChange: (lines: OrderLine[]) => void;
  currency: string;
  showMismatch?: boolean;
}

const emptyLine: OrderLine = {
  description: '',
  unit_price: 0,
  quantity: 1,
  unit: 'pcs',
  stated_total_price: null,
};

export default function OrderLineEditor({ orderLines, onChange, currency, showMismatch = false }: OrderLineEditorProps) {
  const addLine = () => {
    onChange([...orderLines, { ...emptyLine }]);
  };

  const removeLine = (index: number) => {
    onChange(orderLines.filter((_, i) => i !== index));
  };

  const updateLine = (index: number, field: keyof OrderLine, value: string | number | null) => {
    const updated = orderLines.map((line, i) => {
      if (i !== index) return line;
      return { ...line, [field]: value };
    });
    onChange(updated);
  };

  const calculateTotal = (line: OrderLine) => {
    return (line.unit_price * line.quantity).toFixed(2);
  };

  const hasMismatch = (line: OrderLine) => {
    if (!showMismatch || line.stated_total_price === null) return false;
    const calculated = line.unit_price * line.quantity;
    return Math.abs(calculated - line.stated_total_price) > 0.01;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-100">Order Lines</h3>
        <button
          type="button"
          onClick={addLine}
          className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add Line
        </button>
      </div>

      {orderLines.length === 0 ? (
        <div className="text-center py-8 text-gray-400 bg-gray-800 rounded-lg border border-gray-700">
          No order lines yet. Click "Add Line" to add items.
        </div>
      ) : (
        <div className="space-y-3">
          {orderLines.map((line, index) => (
            <div
              key={index}
              className={`bg-gray-800 rounded-lg border p-4 ${
                hasMismatch(line) ? 'border-yellow-500' : 'border-gray-700'
              }`}
            >
              <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
                <div className="md:col-span-2">
                  <label className="block text-xs text-gray-400 mb-1">Description</label>
                  <input
                    type="text"
                    value={line.description}
                    onChange={(e) => updateLine(index, 'description', e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Item description"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Unit Price ({currency})</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={line.unit_price}
                    onChange={(e) => updateLine(index, 'unit_price', parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Quantity</label>
                  <input
                    type="number"
                    step="1"
                    min="1"
                    value={line.quantity}
                    onChange={(e) => updateLine(index, 'quantity', parseInt(e.target.value) || 1)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Unit</label>
                  <select
                    value={line.unit}
                    onChange={(e) => updateLine(index, 'unit', e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="pcs">pcs</option>
                    <option value="kg">kg</option>
                    <option value="m">m</option>
                    <option value="l">l</option>
                    <option value="h">h</option>
                    <option value="set">set</option>
                  </select>
                </div>
                <div className="flex items-end gap-2">
                  <div className="flex-1">
                    <label className="block text-xs text-gray-400 mb-1">Total</label>
                    <div className="px-3 py-2 bg-gray-600 border border-gray-600 rounded-lg text-gray-100">
                      {calculateTotal(line)} {currency}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeLine(index)}
                    className="p-2 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-lg transition-colors"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              </div>
              <div className="mt-3 flex items-end gap-4">
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Stated Total Price (optional)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={line.stated_total_price ?? ''}
                    onChange={(e) => updateLine(index, 'stated_total_price', e.target.value ? parseFloat(e.target.value) : null)}
                    className="w-full md:w-48 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="As stated in document"
                  />
                </div>
                {hasMismatch(line) && (
                  <div className="flex items-center gap-2 text-yellow-400 text-sm pb-2">
                    <AlertTriangle className="h-4 w-4" />
                    <span>
                      Mismatch: stated {line.stated_total_price?.toFixed(2)} vs calculated {calculateTotal(line)} {currency}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {orderLines.length > 0 && (
        <div className="flex justify-end">
          <div className="bg-gray-800 rounded-lg border border-gray-700 px-4 py-2">
            <span className="text-gray-400">Calculated Total: </span>
            <span className="font-bold text-lg">
              {orderLines.reduce((sum, line) => sum + line.unit_price * line.quantity, 0).toFixed(2)} {currency}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
