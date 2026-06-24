import { useCallback } from "react";
import { compile } from "../api/compiler";
import type { AppError } from "../api/errors";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { PipelineVisualization } from "../components/compile/PipelineVisualization";
import { PromptCards } from "../components/compile/PromptCards";
import { PromptEditor } from "../components/compile/PromptEditor";
import { ResultsSkeleton } from "../components/compile/ResultsSkeleton";
import { ResultTabs } from "../components/compile/ResultTabs";
import { useCompileStore } from "../store/compileStore";

const SECTION_TITLE_STYLE = {
  margin: "0 0 var(--space-4)",
  fontSize: 14,
  fontWeight: 700,
  color: "var(--color-text-secondary)",
  textTransform: "uppercase" as const,
  letterSpacing: "0.04em",
};

export function CompilePage() {
  const prompt = useCompileStore((state) => state.prompt);
  const status = useCompileStore((state) => state.status);
  const result = useCompileStore((state) => state.result);
  const error = useCompileStore((state) => state.error);
  const setPrompt = useCompileStore((state) => state.setPrompt);
  const start = useCompileStore((state) => state.start);
  const succeed = useCompileStore((state) => state.succeed);
  const fail = useCompileStore((state) => state.fail);

  const isLoading = status === "loading";

  const runCompile = useCallback(() => {
    const trimmed = prompt.trim();
    if (!trimmed || isLoading) return;

    start();
    compile(trimmed)
      .then(succeed)
      .catch((caught: AppError) => fail(caught));
  }, [prompt, isLoading, start, succeed, fail]);

  const showPipeline = isLoading || result !== null;
  const pipelineStageSummaries = isLoading ? [] : result?.stage_summaries ?? [];

  return (
    <div
      style={{
        maxWidth: 960,
        margin: "0 auto",
        padding: "var(--space-6) var(--space-5)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-6)",
      }}
    >
      <header>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Compile a system from a prompt</h1>
        <p style={{ margin: "var(--space-2) 0 0", fontSize: 13, color: "var(--color-text-secondary)", maxWidth: 640 }}>
          Describe the system you want to build in plain English. The compiler will extract intent,
          design the architecture, generate a data schema, and validate consistency across every stage.
        </p>
      </header>

      <PromptEditor value={prompt} onChange={setPrompt} onSubmit={runCompile} isLoading={isLoading} />

      <PromptCards onSelect={setPrompt} disabled={isLoading} />

      {status === "error" && error && (
        <ErrorBanner message={error.message} detail={error.detail} onRetry={runCompile} />
      )}

      {showPipeline && (
        <section className="fade-in-up">
          <h2 style={SECTION_TITLE_STYLE}>Pipeline</h2>
          <PipelineVisualization stageSummaries={pipelineStageSummaries} isCompiling={isLoading} />
        </section>
      )}

      {isLoading ? (
        <section>
          <h2 style={SECTION_TITLE_STYLE}>Results</h2>
          <ResultsSkeleton />
        </section>
      ) : result ? (
        <section className="fade-in-up">
          <h2 style={SECTION_TITLE_STYLE}>Results</h2>
          <ResultTabs result={result} />
        </section>
      ) : null}
    </div>
  );
}
