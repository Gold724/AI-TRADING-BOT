# Git Best Practices for AI Trading Sentinel

## Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for creating an explicit commit history. Each commit message should be structured as follows:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools and libraries

### Examples

```
feat(api): add endpoint for retrieving trading history
```

```
fix(executor): resolve issue with order placement timing
```

```
docs: update README with deployment instructions
```

```
refactor(frontend): reorganize component structure
```

## Branch Strategy

- **main/master**: Production-ready code
- **develop**: Integration branch for features
- **feature/xxx**: New features (branch from develop)
- **fix/xxx**: Bug fixes (branch from develop or main)
- **release/x.x.x**: Release preparation

## Pull Request Guidelines

1. Keep PRs small and focused on a single feature or fix
2. Include tests for new functionality
3. Ensure all tests pass before requesting review
4. Reference related issues in the PR description

## Commit Frequency

- Commit early and often during development
- Each commit should represent a logical unit of work
- Avoid large commits that change many files or mix unrelated changes
- Consider using `git add -p` to stage specific parts of files

## Git Hooks

Consider setting up pre-commit hooks for:

- Code linting
- Running tests
- Checking commit message format

## Sensitive Data Protection

- **NEVER** commit sensitive data (API keys, passwords, etc.)
- Use `.env.example` to document required environment variables
- Regularly audit the repository for accidentally committed secrets
- Consider using git-secrets or similar tools to prevent committing secrets

## Recommended Git Aliases

Add these to your `.gitconfig` for convenience:

```
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    unstage = reset HEAD --
    last = log -1 HEAD
    visual = !gitk
    hist = log --pretty=format:"%h %ad | %s%d [%an]" --graph --date=short
```

## Git LFS Usage

We use Git LFS for tracking large files. The following file types are currently tracked:

- `*.png`
- `*.zip`
- `*.pt` (PyTorch model files)

To add more file types to LFS tracking:

```bash
git lfs track "*.new-extension"
git add .gitattributes
git commit -m "chore: track new file extension with Git LFS"
```