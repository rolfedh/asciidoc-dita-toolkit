# Aditi plan

Help me write a plan to build complete reboot of asciidoc-dita-toolkit from the ground-up.

Let's call the new application *Aditi*, short for "asciidoc dita intigration". Make this a "white-slate" design, using software architecture best practices. Only borrow or reuse aspects of asciidoc-dita-toolkit that we specify in this plan. Avoid directly copying or being unduly influenced by the implementation of of asciidoc-dita-toolkit. Generally take a creative and critical approach to designing Aditi from scratch. The first iteration of Aditi should be an MVP design. The primary user story is that of the techncial writer who needs to prepare their asciidoc for eventual migration to DITA. Other use cases present in asciidoc-dita-toolkit are not important here. Design a CLI that provides an experience similar to Claude Code.

Side note: Aditi is a Sanskrit name meaning "boundless" or "unlimited". In Hindu mythology, Aditi is a major goddess, often called the mother of the gods: Adityas. She represents infinity, the cosmos, and the boundless potential of the universe.

## Dependencies

### image: ghcr.io/rolfedh/asciidoc-dita-toolkit-prod

Aditi uses a prebuilt Docker container to run Vale linter with the AsciiDocDITA rulest from [asciidoctor-dita-vale](https://github.com/jhradilek/asciidoctor-dita-vale) against a set of asciidoctor (*.adoc) files in a git repository.

Currently, I use /home/rolfedh/asciidoc-dita-toolkit/.github/workflows/container-build.yml to build and publish the images.Despite the workflow having push triggers commented out, I have run it manually has run successfully multiple times recently, including on July 20, 2025. The workflow builds:
- Production image: ghcr.io/rolfedh/asciidoc-dita-toolkit-prod
- Vale-adv image:
  ghcr.io/rolfedh/asciidoc-dita-toolkit-vale-adv

Aditi should reuse /home/rolfedh/asciidoc-dita-toolkit/.github/workflows/container-build.yml.

I also created issue #97: https://github.com/jhradilek/asciidoctor-dita-vale/issues/97 asking Jaromir to take over this responsiblity, republishing the images after he makes significant changes to the ruleset. When he does that, I'll update Aditi to use his images instead.

### Python and PyPi

I will publish Aditi on PyPi by entering a `make publish` command.
Reuse the `make publish` workflow and supporting scripts defined in /home/rolfedh/asciidoc-dita-toolkit/Makefile.

The user's Mac or Linux computer must have a recent version of Python3 (3.7 or later).
(We don't support Microsoft Windows.)

### Ruby?

Almost all the code is Python3. However one recent pull request includes Ruby. If merged, the user's computer must have a recent version of Ruby.

### Git integration

Aditi will automate git actions like checking out the main branch, getting the latest changes, creating a feature branch, committing changes, pushing changes and creating a pull request.

The user's computer must have `glab` to work with **GitLab** instances: https://gitlab.com/gitlab-org/cli/-/tree/github-actions-to-gitlab-ci

QUESTION: Do users need support for **GitHub**? If so, the user's computer must have `gh` to work with GitHub: https://gitlab.com/gitlab-org/cli/-/tree/github-actions-to-gitlab-ci

## AsciiDocDITA rule violations, fixing or flagging violations, and git workflow

The AsciiDocDITA ruleset flags specific violations that must or should be fixed before the user can migrate the *.adoc files content to DITA and Adobe Experience Manager (AEM). Otherwise, if violations are not fixed now, they will cause errors or warnings in the future when the user tries to import the asciidoc content to DITA.

Aditi either fixes or flags AsciiDocDITA rule violations. I characterize these fixes three different ways: fully deterministic fixes, partially deterministic fixes, and non-deterministic fixes.

### How Aditi flags violations

When Aditi flags a unresolved violations, it indexes the file from the bottom, inserting a comment on the line above the lowest violation first and working its way up. (This approach ensures that the comment lands on the line above the violation. Otherwise, if you index from the top and insert comments, the content starts "sliding down" such that each new comment lands one additional line above its intended target, with the two drifting farther and farther apart.)

This is also why we run only one rule at a time.

The comment names the rule, provides concise instructions, and gives the URL of an additional resource. For example:
```
// Rule: ExampleBlock - DITA 1.3 allows the <section> element to appear only within the main body of the topic. For instructions, see https://docs.asciidoctor.org/asciidoc/latest/sections/titles-and-levels/
```

### Fully deterministic fixes

Some of the violations have **fully deterministic fixes**. For example, the [EntityReference rule](#entityreference-rule) detects character entity references that DITA does not support. The deterministic fix is to replace those unsupported character entity references with ones that are supported. Aditi can make fully deterministic fixes practically 100% of the time. After completing the fixes, Aditi reruns the matching AsciiDocDITA rule, and the results should show zero violations.

Other AsciiDocDITA rules that (seem to) have fully deterministic fixes include:

- TBD
- TBD

Git workflow: Create a working branch. For each AsciiDocDITA rule that has fully deterministic fixes:

1. Aditi runs the rule and makes the fixes.
2. Aditi reruns the rule to confirm the fixes.
  - Aditi expects zero violations for the rule. However, if Aditi it detects an unfixed violation, it flags the violation with a comment and logs it in ./reports/<rulename>.md.
3. Aditi commits the changes. The commit message mentions the rule name.
4. When Aditi has finished repeating this process for each rule with fully deterministic fixes, it publishes the branch and creates a PR for it. The PR summary mentions the rule names.
6. Aditi prompts the user to review the PR, fix any unresolved issues, and merge the changes.
7. Aditi asks the user to notify it when the PR has been merged.
6. The user fixes the issues by editing the files and rerunning the rule to display any remaining violations on stdout. When no violations remain, the user pushes the fixes to the PR and merges it.
7. When the user notifies it that the PR has been merged, Aditi checks out the main branch,reruns the complete set of rules that have fully deterministic fixes, notifies the user of any unresolved issues and asks the user if they want to fix the issue (return to step 1) or mark this stage as done and continue to the set of rules.

(QUESTION: Should we group rules in stages? Some rules, regardless of how deterministic their fixes are, must run before others. For example, the user must address ContentType violations before running rules that depend on having the content type correctly defined. Therefore, though we might group some rules by their "determinisitic type", we might group other rules by the sequence in which they must be run. Let's call these groupings "stages".)

### partially deterministic fixes

Other violations have **partially deterministic fixes**. For example, the [ContentType rule](#contenttype-rule) detects missing `:_mod-docs-content-type:` attributes; and it detects when the value of this attribute is missing or unsupported. Deterministic fixes include:
- if the `:_mod-docs-content-type:` attribute is missing, Aditi inserts it in the correct location.
- if the `:_mod-docs-content-type:` attribute is in the wrong location, Aditi moves it to the correct location.
- if the value of the `:_mod-docs-content-type:` attribute is missing or invalid, Aditi determines a correct attribute value and appends it to the attribute. Aditi determines the correct value as follows:
  1. If a deprecated attribute such as TBD or TBD is present, Aditi assigns the value of that attribute to `:_mod-docs-content-type:`. Then, it deletes the deprecated attribute and its value.
  2. If the filename contains a valid prefix (`proc`,`conc`,`task`,`assembly`,`assy`,`snip`) followed by an underscore or dash (`_` or `-`) it uses this to determine the appropriate `:_mod-docs-content-type:` value.
  3. If none of the above produces a valid attribute value, Aditi must assign a placeholder value, `TBD`, to `:_mod-docs-content-type:`. (Later, when the user reviews all the changes, the user must replace `TBD` with a valid value: `CONC`, `TASK`, `ASS`, `SNIP`, `PROC`)

In other words, for **partially deterministic fixes**, Aditi can fix the violation or insert a parital fix that might include a `TBD` **placeholder**. Aditi must also flag the issue by inserting a comment on the line above the violation.

After performing these operations, Aditi reruns the matching AsciiDocDITA rule and the results should show only violations that include placeholders like `TBD` and those violations must all have matching comments.
The user must search for these placeholders and comments and fix the violations. The user should periodically have Aditi rerun the matching rule until there are zero violations. Then the user can ask Aditi to clean up the comments. Finally the user can push the changes to a PR and merge it.

Git workflow: Create a working branch. For each AsciiDocDITA rule that has partially deterministic fixes:

1. Aditi runs the rule and makes the fixes or inserts placeholders and flags violations.
2. Aditi commits the changes. The commit message mentions the rule name.
3. Aditi publishes the branch and creates a PR for it. The PR summary mentions the rule name.
4. Aditi prompts the user to review the PR, fix any unresolved issues, and merge the changes.
5. Aditi asks the user to notify it when the PR has been merged.
6. The user fixes the issues by editing the files and rerunning the rule to display any remaining violations on stdout. When no violations remain, the user pushes the fixes to the PR and merges it.
7. When the user notifies it that the PR has been merged, Aditi checks out the main branch,reruns the rule, notifies the user of any unresolved issues and asks the user if they want to fix the issue (return to step 1) or mark this rule as done and continue to the next rule.

### Non-deterministic fixes

Finally, some rule violations have **non-deterministic fixes**. In this case, Aditi flags the violations and the user fixes them.


1. Aditi runs the rule and flags the violations.
2. Aditi commits the changes. The commit message mentions the rule name.
3. Aditi publishes the branch and creates a PR for it. The PR summary mentions the rule name.
4. Aditi prompts the user to review the PR, fix any unresolved issues, and merge the changes.
5. Aditi asks the user to notify it when the PR has been merged.
6. The user fixes the issues by editing the files and rerunning the rule to display any remaining violations on stdout. When no violations remain, the user pushes the fixes to the PR and merges it.
7. When the user notifies it that the PR has been merged, Aditi checks out the main branch,reruns the rule, notifies the user of any unresolved issues and asks the user if they want to fix the issue (return to step 1) or mark this rule as done and continue to the next rule.


## Sequence of operations


### Stage 1: Configuration (Aditi CLI Interaction Example)

User enters: `aditi journey`

```bash
Aditi: "Welcome to Aditi! Let's set up your documentation migration journey."
Aditi: "Step 1: Use `cd` to navigate to the root directory of your documentation repository. Enter `done` when finished."
User: (navigates to the directory and enters `done`.)

Aditi: "Step 2: Check out your repository's default branch. For example, enter `git checkout main`.  Enter `done` when finished."
User: (runs command and enters `done`.)

Aditi: "Step 3: Specify any release branches you plan to update, separated by commas. For example, `release-123, release-456`. Enter `done` when finished."
User: `quarkus-3-15, quarkus-3-20`

Aditi: "Step 4: Update your branches. Run:
git fetch upstream
git rebase upstream/main
git checkout quarkus-3-15
git rebase upstream/quarkus-3-15
git checkout quarkus-3-20
git rebase upstream/quarkus-3-20"
Aditi: "Enter `done` when finished."

User: (runs command and presses Enter)

Aditi: "Step 5: Please confirm the following information:"
Aditi: "  - Repository root: /home/rolfedh/my-docs-repo"
Aditi: "  - Default branch: main"
Aditi: "  - Release branches: release-2025, hotfix-2025-07"
Aditi: "Is this correct? (Y/n)"
User: `y`

Aditi: "Saved configuration to ~/aditi-data/config.json..."

Aditi: "Step 6: By default, Aditi will run in your repository root and all subdirectories."
Aditi: "Would you like to allow or block specific subdirectories? (yes/no)"
User: `yes`

Aditi: "Enter `allow: <directory_path>` or `block: <directory_path>` for each directory. Enter `done` when finished."
User:
allow: docs/user-guide
allow: docs/api
block: docs/drafts
done

Aditi: "Here are your subdirectory permissions:"
Aditi: "  - Allowed: docs/user-guide, docs/api"
Aditi: "  - Blocked: docs/drafts"
Aditi: "Confirm these choices? (yes/no)"
User: `yes`

Aditi: "Saving updated configuration to ~/aditi-data/config.json and creating a timestamped backup."

Aditi: "Step 7: Please enter a name for your feature branch (e.g., `aditi-contenttype-fix`):"
User: `aditi-contenttype-fix`

Aditi: "Creating feature branch: aditi-contenttype-fix"
Aditi: "Configuration complete! You are ready to begin your migration journey."
```

For example:
```json
{
  "repo_root": "/home/rolfedh/my-docs-repo",
  "default_branch": "main",
  "release_branches": ["release-123", "release-456"],
  "subdirectory_permissions": {
    // "allow": ["docs/assemblies", "docs/modules"],
    // "block": ["docs/archive"]
  },
  "feature_branch": "aditi-contenttype-fix",
  "notes": [
    "Update this file whenever you change configuration.",
    "Each update should be backed up with a timestamped copy."
  ]
}
```

### Stage 2: Prerequisites

#### ContentType rule

ContentType: Without a clear content type definition, the Vale style cannot reliably report problems related to procedure modules such as `TaskSection` or `TaskExample`. Add the correct `:_mod-docs-content-type:` definition at the top of the file.

Valid attribute values:
- `ASSEMBLY`
- `CONCEPT`
- `PROCEDURE`
- `REFERENCE`
- `SNIPPET`

Placeholder non-valid attribute value:
- `TBD`

Obsolete or deprecated attribute names:
- `:_content-type:`
- `:_module-type:`

Fix type: partially deterministic fixes

Fixtures path: https://github.com/jhradilek/asciidoctor-dita-vale/tree/main/fixtures/ContentType

Develop regex rules:
- Use the files named `report*.doc` to detect rule violations.
- Use the files named `ignore*.doc` to exclude rule violations.

Fixes:
- For https://raw.githubusercontent.com/jhradilek/asciidoctor-dita-vale/refs/heads/main/fixtures/ContentType/report_comments.adoc, uncomment the line that contains `:_mod-docs-content-type:`
- For https://raw.githubusercontent.com/jhradilek/asciidoctor-dita-vale/refs/heads/main/fixtures/ContentType/report_missing_type.adoc insert `:_mod-docs-content-type:`.
- For - For https://raw.githubusercontent.com/jhradilek/asciidoctor-dita-vale/refs/heads/main/fixtures/ContentType/report_missing_type.adoc and https://raw.githubusercontent.com/jhradilek/asciidoctor-dita-vale/refs/heads/main/fixtures/ContentType/report_missing_value.adoc, assign a valid value based on the `detect_existing_attribute` or `filename_prefixes`. Otherwise, assign `TBD`, a non-valid placeholder value.

Use the following code or some variation of it for inspiration, at your discretion:

```python
    def get_default(cls) -> 'ContentTypeConfig':
        """Get default configuration for content type detection."""
        return cls(
            filename_prefixes={
                ("assembly_", "assembly-"): "ASSEMBLY",
                ("con_", "con-"): "CONCEPT",
                ("proc_", "proc-"): "PROCEDURE",
                ("ref_", "ref-"): "REFERENCE",
                ("snip_", "snip-"): "SNIPPET",
            },
        )
```

```python
    def detect_existing_attribute(
        self, lines: List[Tuple[str, str]]
    ) -> Optional[ContentTypeAttribute]:
        """
        Detect existing content type attributes in file.

        Args:
            lines: List of (text, ending) tuples from file

        Returns:
            ContentTypeAttribute or None if not found
        """
        logger.debug("Detecting existing content type attributes")

        for i, (text, _) in enumerate(lines):
            stripped = text.strip()

            # Current format
            if stripped.startswith(":_mod-docs-content-type:"):
                value = stripped.split(":", 2)[-1].strip()
                logger.debug("Found current format content type: %s", value)
                return ContentTypeAttribute(value, i, 'current')

            # Commented-out current format
            if stripped.startswith("//:_mod-docs-content-type:"):
                value = stripped.split(":", 2)[-1].strip()
                logger.debug("Found commented content type: %s", value)
                return ContentTypeAttribute(value, i, 'commented')

            # Deprecated formats
            if stripped.startswith(":_content-type:"):
                value = stripped.split(":", 2)[-1].strip()
                logger.debug("Found deprecated content-type: %s", value)
                return ContentTypeAttribute(value, i, 'deprecated_content')

            if stripped.startswith(":_module-type:"):
                value = stripped.split(":", 2)[-1].strip()
                logger.debug("Found deprecated module-type: %s", value)
                return ContentTypeAttribute(value, i, 'deprecated_module')

        logger.debug("No existing content type attributes found")
        return None
```

- Ensure `:_mod-docs-content-type:` is followed by a blank line. Add one, if needed.

Based on the [asciidoctor-dita-vale available rules](https://github.com/jhradilek/asciidoctor-dita-vale?tab=readme-ov-file#available-rules):

**ContentType** is a prerequisite for several other rules, because many rules depend on the correct identification of the module type. The **TaskSection**, **TaskExample**, **TaskStep**, **TaskTitle**, and **TaskDuplicate** rules only apply to modules identified as procedures (i.e., files with `:_mod-docs-content-type: PROCEDURE` attribute). Otherwise, if this attribute is missing or incorrect, these rules cannot reliably detect or fix violations.

## About asciidoctor-dita-vale fixtures (TODO Move section selsewhere)

Reuse the following files from /home/rolfedh/asciidoc-dita-toolkit to get the latest fixtures from https://github.com/jhradilek/asciidoctor-dita-vale/tree/main/fixtures:

- /home/rolfedh/asciidoc-dita-toolkit/.github/workflows/fetch-fixtures.yml
- /home/rolfedh/asciidoc-dita-toolkit/archive/fetch-fixtures.sh

Run a GitHub action to get these weekly. Create a PR if there are any changes.

## EntityReference rule

EntityReference: DITA 1.3 supports five character entity references defined in the XML standard: &amp;, &lt;, &gt;, &apos;, and &quot;. Replace any other character entity references with [an appropriate built-in AsciiDoc attribute](https://docs.asciidoctor.org/asciidoc/latest/attributes/character-replacement-ref/).
