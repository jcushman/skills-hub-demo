# Legal Ed Agent Skills Hub

A collection of AI agent skills for legal education, built by the [Harvard Law School Library Innovation Lab](https://lil.law.harvard.edu/).

## Why This Exists

People are already using AI to learn the law -- to prepare for class, study for exams, understand legal issues, build professional skills. Much of that use happens without pedagogical guidance: the AI helps, but no one has thought carefully about *how* it should help for a given educational context.

This project explores what it looks like to bring sound pedagogy to AI-assisted legal education. The vehicle is **agent skills** -- modular capabilities you install into an AI coding or writing assistant. Each skill encodes a pedagogical approach: not just "help me with X," but "help me with X in a way that builds understanding / develops capability / orients me toward the right resources."

### Skills as markdown, not software

A skill is a markdown file. It contains instructions that shape how an AI agent approaches a task -- what questions to ask, what steps to follow, what tone to use, what to avoid. Writing a skill is closer to writing a lesson plan than writing code.

This matters because the people who know how law should be taught -- professors, clinical faculty, librarians, practitioners -- are mostly not software developers. By structuring legal edtech as markdown files with clear conventions, subject matter experts can create, review, and iterate on AI-assisted educational tools directly, without writing code or depending on engineers.

### Rapid exploration

Each skill is a self-contained experiment in AI-assisted pedagogy. You can write one in an afternoon, test it immediately, and iterate based on what works. The collection can grow to dozens of skills across different educational contexts without any of them depending on each other. This makes it practical to explore a wide range of approaches quickly -- traditional Socratic methods alongside evidence-based designs, student coaching alongside professional development, legal information alongside legal research training.

## How It Works

### Personas

Skills are organized by **persona** -- the role someone occupies when using them. Each persona has a **pedagogical objective** that shapes every skill in the collection: not just what the skills do, but how they do it.

| Persona | Objective | Key constraint |
|---------|-----------|----------------|
| **Professor** | Improve the quality of legal education | Help design learning experiences, not produce student-facing work product |
| **Student** | Coach, encourage, and check understanding | Never produce finished work product the student would submit |
| **Pro Se** | Orient and connect | Never give legal advice; teach, orient, and empower |
| **CLE** | Coach and build skills | Build the attorney's own capabilities, not do work for them |

The pedagogical objectives are design constraints, not labels. A pro-se skill should never do legal research *for* the user; it should teach them how to find relevant information and connect them with professional help. A student skill should coach rather than produce finished answers. These constraints are defined in `skills/personas.yaml` alongside design principles, tone guidance, and success criteria for each persona.

### Meta skills: making the collection sticky

Individual skills do one job well, but they're forgettable -- you have to remember they exist and go find them. A **meta skill** solves this by acting as an ambient capability layer for an entire persona.

You install one meta skill for your role. From that point on:

1. You describe tasks normally ("I need to build a syllabus," "check if I understand this case").
2. The meta skill triggers on any task within the persona's domain.
3. It checks whether a specialized skill is already installed that handles the task.
4. If yes: it defers to that skill.
5. If no: it fetches the persona's inventory from a live JSON endpoint and recommends relevant skills with install links.
6. If nothing matches: it assists directly, guided by the persona's pedagogical objective.

The user never has to remember skill names or revisit the website. The meta skill handles discovery, making the collection feel like an always-available set of competencies rather than a catalog you visit once.

### Skill format

Each skill is a folder with a `SKILL.md` file and optional reference material. The SKILL.md has YAML frontmatter (`name` and `description` -- the trigger that tells the agent when to activate the skill) and a markdown body (the instructions the agent follows after activation). No code required.

## Skills in This Collection

### Professor

- **Syllabus Traditional** -- Creates a conventional Socratic law school syllabus from provided course materials, using linear doctrinal sequencing and casebook ordering.
- **Syllabus Evidence-Based** -- Creates a modern syllabus using spiral structure, spaced practice, interleaving, and backward design drawn from learning science research.

### Student

- **Understanding Check** -- Conducts a structured diagnostic to identify gaps and misconceptions halfway through a course.
- **Exam Answer Eval** -- Evaluates a practice exam answer along standard law school dimensions (issue-spotting, analysis, counterarguments) with specific, actionable feedback.
- **Socratic Tutor** -- Conducts a Socratic dialogue on assigned readings to prepare for class.

### Pro Se

- **Issue Interview** -- A structured intake interview that helps someone understand their legal issue in plain language and prepare to seek help.
- **Research Coach** -- Teaches how to find and read relevant law, rather than doing the research for them.

### CLE

- **Development Plan** -- Creates a structured professional development plan with quarterly milestones.
- **Topic Curriculum** -- Builds a self-study curriculum for transitioning into a new practice area.
- **Client Email Coach** -- Reviews draft client emails with specific feedback on clarity, tone, and risk management.

## Development

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
# Build the site locally (relative URLs)
uv run scripts/build.py

# Build for deployment (absolute URLs)
uv run scripts/build.py --base-url https://example.github.io/skills-hub-demo/

# Preview
uv run python -m http.server -d _site
```

The build script reads `skills/` and produces `_site/` containing `.skill` zip files, JSON inventories, and the static website. The website is deployed to GitHub Pages automatically on push to `main`.

## License

TBD
