import type { Project } from "../../shared/types";

export function ProjectSelect({ projects, value, onChange }: { projects: Project[]; value: string | null; onChange: (value: string | null) => void }) {
  return <label>Project<select value={value ?? ""} onChange={(event) => onChange(event.target.value || null)}><option value="">Unassigned</option>{projects.filter((project) => !project.archived_at || project.id === value).map((project) => <option key={project.id} value={project.id}>{project.name}{project.archived_at ? " (archived)" : ""}</option>)}</select></label>;
}
