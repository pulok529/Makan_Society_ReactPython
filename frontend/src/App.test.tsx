import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { App } from "./App";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

const queryClient = new QueryClient();

describe("App component smoke test", () => {
  it("renders without crashing", () => {
    // We only need to check if it renders without throwing an error
    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    );
    expect(container).toBeTruthy();
  });
});
