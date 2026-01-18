import RequestForm from '../components/RequestForm';

export default function NewRequest() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-100 mb-6">New Procurement Request</h1>
      <RequestForm editMode={false} />
    </div>
  );
}
