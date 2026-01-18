import { useParams, useNavigate } from 'react-router-dom';
import RequestForm from '../components/RequestForm';

export default function EditRequest() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  if (!id) {
    navigate('/overview');
    return null;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-100 mb-6">Edit Request #{id}</h1>
      <RequestForm editMode={true} requestId={parseInt(id)} />
    </div>
  );
}
