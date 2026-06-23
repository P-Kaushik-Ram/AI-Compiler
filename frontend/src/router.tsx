import { Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { CompilePage } from "./pages/CompilePage";
import { EvaluationPage } from "./pages/EvaluationPage";
import { NotFoundPage } from "./pages/NotFoundPage";

/** Route-agnostic so tests can wrap it in a MemoryRouter; App.tsx supplies the BrowserRouter. */
export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<CompilePage />} />
        <Route path="/evaluate" element={<EvaluationPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
