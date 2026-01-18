import { Link } from 'react-router-dom';
import { PlusCircle, List, Package } from 'lucide-react';

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <div className="text-center mb-12">
        <div className="flex items-center justify-center gap-3 mb-4">
          <Package className="h-16 w-16 text-blue-500" />
        </div>
        <h1 className="text-4xl font-bold text-gray-100 mb-2">Welcome to Procuro</h1>
        <p className="text-xl text-gray-400">
          Procurement Request Management System
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 w-full max-w-2xl">
        <Link
          to="/new"
          className="flex flex-col items-center gap-4 p-8 bg-gray-800 rounded-xl border border-gray-700 hover:border-blue-500 hover:bg-gray-750 transition-all group"
        >
          <div className="p-4 bg-blue-600 rounded-full group-hover:scale-110 transition-transform">
            <PlusCircle className="h-8 w-8" />
          </div>
          <div className="text-center">
            <h2 className="text-xl font-semibold text-gray-100">New Request</h2>
            <p className="text-gray-400 mt-1">Create a new procurement request</p>
          </div>
        </Link>

        <Link
          to="/overview"
          className="flex flex-col items-center gap-4 p-8 bg-gray-800 rounded-xl border border-gray-700 hover:border-blue-500 hover:bg-gray-750 transition-all group"
        >
          <div className="p-4 bg-green-600 rounded-full group-hover:scale-110 transition-transform">
            <List className="h-8 w-8" />
          </div>
          <div className="text-center">
            <h2 className="text-xl font-semibold text-gray-100">Overview</h2>
            <p className="text-gray-400 mt-1">View and manage all requests</p>
          </div>
        </Link>
      </div>
    </div>
  );
}
