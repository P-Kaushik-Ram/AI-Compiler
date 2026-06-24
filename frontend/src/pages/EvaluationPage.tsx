import { BarChart3, Loader2, Play } from "lucide-react";
import { useCallback, useMemo } from "react";
import { evaluate } from "../api/evaluation";
import type { AppError } from "../api/errors";
import { EmptyState } from "../components/common/EmptyState";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { BenchmarkBreakdown } from "../components/evaluation/BenchmarkBreakdown";
import { BenchmarkSummary } from "../components/evaluation/BenchmarkSummary";
import { CustomDatasetEditor } from "../components/evaluation/CustomDatasetEditor";
import { EvaluationSkeleton } from "../components/evaluation/EvaluationSkeleton";
import { PresetSelector } from "../components/evaluation/PresetSelector";
import { StageDistributionTable } from "../components/evaluation/StageDistributionTable";
import { getPreset, parseCustomDataset } from "../lib/evaluationPresets";
import { useEvaluationStore } from "../store/evaluationStore";
import type { DatasetCase } from "../types/evaluation";

const SECTION_TITLE_STYLE = {
  margin: "0 0 var(--space-4)",
  fontSize: 14,
  fontWeight: 700,
  color: "var(--color-text-secondary)",
  textTransform: "uppercase" as const,
  letterSpacing: "0.04em",
};

interface ResolvedDataset {
  datasetName: string;
  cases: DatasetCase[];
}

export function EvaluationPage() {
  const preset = useEvaluationStore((state) => state.preset);
  const customInput = useEvaluationStore((state) => state.customInput);
  const status = useEvaluationStore((state) => state.status);
  const result = useEvaluationStore((state) => state.result);
  const error = useEvaluationStore((state) => state.error);
  const setPreset = useEvaluationStore((state) => state.setPreset);
  const setCustomInput = useEvaluationStore((state) => state.setCustomInput);
  const start = useEvaluationStore((state) => state.start);
  const succeed = useEvaluationStore((state) => state.succeed);
  const fail = useEvaluationStore((state) => state.fail);

  const isLoading = status === "loading";

  const dataset: ResolvedDataset | null = useMemo(() => {
    if (preset === "custom") {
      const cases = parseCustomDataset(customInput);
      return cases.length > 0 ? { datasetName: "custom-dataset", cases } : null;
    }
    const definition = getPreset(preset);
    return { datasetName: definition.datasetName, cases: definition.cases };
  }, [preset, customInput]);

  const canRun = dataset !== null && !isLoading;

  const runEvaluation = useCallback(() => {
    if (!dataset || isLoading) return;
    start();
    evaluate(dataset.datasetName, dataset.cases)
      .then(succeed)
      .catch((caught: AppError) => fail(caught));
  }, [dataset, isLoading, start, succeed, fail]);

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
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Evaluate the compiler against a dataset</h1>
        <p style={{ margin: "var(--space-2) 0 0", fontSize: 13, color: "var(--color-text-secondary)", maxWidth: 640 }}>
          Pick a benchmark preset or enter your own prompts. Every case is streamed through the same
          compiler pipeline used by the Compile page and folded into one aggregate BenchmarkResult.
        </p>
      </header>

      <section>
        <h2 style={SECTION_TITLE_STYLE}>Dataset</h2>
        <PresetSelector value={preset} onChange={setPreset} disabled={isLoading} />

        {preset === "custom" && (
          <div style={{ marginTop: "var(--space-4)" }}>
            <CustomDatasetEditor value={customInput} onChange={setCustomInput} disabled={isLoading} />
          </div>
        )}

        <div
          style={{
            marginTop: "var(--space-4)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "var(--space-3)",
            flexWrap: "wrap",
          }}
        >
          <span style={{ fontSize: 12, color: "var(--color-text-secondary)", fontFamily: "var(--font-mono)" }}>
            {dataset
              ? `${dataset.cases.length} case${dataset.cases.length === 1 ? "" : "s"} ready`
              : "Enter at least one prompt to run an evaluation."}
          </span>
          <button
            type="button"
            className="compile-button"
            onClick={runEvaluation}
            disabled={!canRun}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "var(--space-2)",
              padding: "10px 18px",
              borderRadius: "var(--radius-md)",
              border: "none",
              background: canRun ? "var(--color-brand)" : "var(--color-surface-2)",
              color: canRun ? "#fff" : "var(--color-text-secondary)",
              fontSize: 13,
              fontWeight: 600,
              cursor: canRun ? "pointer" : "not-allowed",
              transition: "filter 0.15s ease",
              flexShrink: 0,
            }}
          >
            {isLoading ? (
              <>
                <Loader2 className="spin" size={14} />
                Running…
              </>
            ) : (
              <>
                <Play size={14} />
                Run Evaluation
              </>
            )}
          </button>
        </div>
      </section>

      {status === "error" && error && (
        <ErrorBanner message={error.message} detail={error.detail} onRetry={runEvaluation} />
      )}

      {isLoading ? (
        <section>
          <h2 style={SECTION_TITLE_STYLE}>Results</h2>
          <EvaluationSkeleton />
        </section>
      ) : result ? (
        <section className="fade-in-up">
          <h2 style={SECTION_TITLE_STYLE}>Results</h2>
          <BenchmarkSummary result={result} />
          <StageDistributionTable result={result} />
          <BenchmarkBreakdown result={result} />
        </section>
      ) : status === "idle" ? (
        <EmptyState
          icon={BarChart3}
          title="No evaluation run yet"
          description="Choose a dataset above and click Run Evaluation to see benchmark metrics."
        />
      ) : null}
    </div>
  );
}
