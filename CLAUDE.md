# Conventions du projet

## Commits sémantiques (Conventional Commits)

Tous les commits suivent la spec [Conventional Commits](https://www.conventionalcommits.org/) :

```
<type>(<scope>): <description courte à l'impératif>

<corps optionnel>
```

- **Types** : `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`, `perf`, `build`
- **scope** optionnel mais recommandé (ex. `scraper`, `deps`, `db`, `webapp`)
- **description** en français, à l'impératif, minuscule, sans point final
- Exemples réels : `fix(scraper): zones parenthésées et dates multi-jours`, `chore(deps): Bump actions/download-artifact from 4 to 8`

## Workflow git

- **Jamais de commit direct sur `main`** : toujours une branche + PR.
- Squash-merge des PR.
- Pour fermer une issue depuis une PR, utiliser les mots-clés **anglais** : `Closes #xx` / `Fixes #xx` (« Ferme » ne déclenche pas l'auto-fermeture GitHub).
