import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import NewRequest from './pages/NewRequest';
import EditRequest from './pages/EditRequest';
import Overview from './pages/Overview';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/new" element={<NewRequest />} />
          <Route path="/overview" element={<Overview />} />
          <Route path="/edit/:id" element={<EditRequest />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
