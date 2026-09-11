"use client";

import { useEffect, useRef, useState } from "react";

type State<T> =
  | { status: "loading"; data: null; error: null }
  | { status: "success"; data: T; error: null }
  | { status: "error"; data: null; error: string };

export function useApi<T>(loader: () => Promise<T>, deps: unknown[] = []): State<T> {
  const [state, setState] = useState<State<T>>({ status: "loading", data: null, error: null });
  const loaderRef = useRef(loader);

  useEffect(() => {
    loaderRef.current = loader;
  });

  useEffect(() => {
    let cancelled = false;
    // Resetting to loading on dep change is intentional: the effect re-runs
    // for a new loader, and the async callbacks below update the final state.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setState({ status: "loading", data: null, error: null });
    loaderRef.current()
      .then((data) => {
        if (!cancelled) setState({ status: "success", data, error: null });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            status: "error",
            data: null,
            error: err instanceof Error ? err.message : String(err),
          });
        }
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}