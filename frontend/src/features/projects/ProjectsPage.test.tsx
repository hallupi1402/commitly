import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ProjectsPage } from "./ProjectsPage";

const mock = vi.hoisted(() => ({ getProjects: vi.fn(), saveProjects: vi.fn(), resolveProjects: vi.fn(), getJournal: vi.fn(), saveJournal: vi.fn() }));
vi.mock("../../shared/journalApi", () => mock);
vi.mock("../../shared/api", async (load) => ({ ...(await load<typeof import("../../shared/api")>()), api: vi.fn() }));

describe("ProjectsPage", () => {
  beforeEach(() => {
    mock.getProjects.mockResolvedValue({ data: [], etag: '"p0"' });
    mock.saveProjects.mockImplementation(async (items) => ({ data: items, etag: '"p1"' }));
    vi.spyOn(window, "confirm").mockReturnValue(true);
  });
  it("creates and archives a project without deleting its history", async () => {
    const user = userEvent.setup();
    render(<ProjectsPage />);
    await user.type(await screen.findByLabelText("New project"), "Commitly");
    await user.click(screen.getByRole("button", { name: "Create project" }));
    expect(await screen.findByRole("heading", { name: "Commitly" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Archive" }));
    expect(await screen.findByText("Archived")).toBeInTheDocument();
  });
});
