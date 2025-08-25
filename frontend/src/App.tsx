import { h } from "preact";
import { Router, Route } from "preact-iso/router";
import Ask from "./components/Ask.tsx";
import Ingest from "./components/Ingest.tsx";
import { LocationProvider } from "preact-iso";

export function App() {
  return (
    <div>
      <h2>Flower Medicine Q&amp;A</h2>
      <hr />
      <LocationProvider>
        <Router>
          <Route path="/" component={Ask} />
          <Route path="/admin" component={Ingest} />
        </Router>
      </LocationProvider>
    </div>
  );
}
