import RequestList from '../components/RequestList';

export default function Overview() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-100 mb-6">Request Overview</h1>
      <RequestList />
    </div>
  );
}
