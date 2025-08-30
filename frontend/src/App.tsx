import { BrowserRouter, Route, Routes } from "react-router";
import Conversation from './components/Conversation.tsx';
import Ingest from './components/Ingest.tsx';

function App() {
  return (
    <BrowserRouter>
      <main className="flex flex-col h-dvh">
        <header className="w-full border-b-primary border-2 py-2 px-2">
          <h3 className="text-xl font-bold text-primary">Zenji</h3>
        </header>
        <div className="flex flex-col px-2 items-center justify-center flex-1 max-h-[95vh]">
          <Routes>
            <Route path="/" element={<Conversation />} />
            <Route path="/ingest" element={<Ingest />} />
          </Routes>
        </div>
      </main>
    </BrowserRouter>
  )
}

export default App;
