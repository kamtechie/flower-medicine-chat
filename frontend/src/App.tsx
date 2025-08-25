import { h } from "preact";
import { Router, Route } from "preact-iso/router";
import Ask from "./components/Ask.tsx";
import Ingest from "./components/Ingest.tsx";
import { LocationProvider } from "preact-iso";

export function App() {
  return (
    <main className="flex flex-col min-h-screen px-4 items-center justify-center">
      <div className="mb-6 flex flex-col items-center">
        <h2 className="text-3xl font-bold drop-shadow-lg bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent mb-2">
          Flower Medicine Q&amp;A
        </h2>
        <div className="w-16 h-1 rounded-full bg-gradient-to-r from-primary to-accent mb-2" />
      </div>
      <div className="w-full max-w-[900px]">
        <LocationProvider>
          <Router>
            <Route path="/" component={Ask} />
            <Route path="/admin" component={Ingest} />
          </Router>
        </LocationProvider>
      </div>
    </main>
  );
}
