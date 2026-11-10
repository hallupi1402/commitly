import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RepositoriesPage } from "./RepositoriesPage";

const mock = vi.hoisted(() => ({ getRepositories: vi.fn(), addRepository: vi.fn(), removeRepository: vi.fn() }));
vi.mock("../../shared/reportApi", () => mock);

describe("RepositoriesPage", () => {
  it("registers only the explicitly selected repository path", async () => {
    mock.getRepositories.mockResolvedValueOnce([]).mockResolvedValueOnce([{ id: "r1", path: "/src/demo", display_name: "demo", remote_name: "origin", author_email: "dev@example.test", last_fetch_at: null, last_fetch_status: "never", last_error: null }]);
    mock.addRepository.mockResolvedValue({});
    const user = userEvent.setup();
    render(<RepositoriesPage />);
    await user.type(await screen.findByLabelText("Repository folder path"), "/src/demo");
    await user.click(screen.getByRole("button", { name: "Select repository" }));
    expect(mock.addRepository).toHaveBeenCalledWith("/src/demo", "origin");
    expect(await screen.findByText("dev@example.test")).toBeInTheDocument();
  });
});
